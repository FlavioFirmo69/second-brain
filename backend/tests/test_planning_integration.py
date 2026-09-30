"""Run only against a disposable PostgreSQL database, never production.
Set TEST_DATABASE_URL after installing schema 005 and migration 013.
"""
import asyncio
import json
import os
from datetime import date, datetime
from uuid import uuid4
import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from app import planning
from app.calendar_rules import apply_calendar_rules
from app.repository import Repository
from app.planning_models import CaseInput, PlanInput, DraftInput, RevisionInput, TurnInput, CoverageInput
from app.schemas import TaskCreate, EventCreate
from test_planning import make_draft


@pytest.fixture
def db(monkeypatch):
    url=os.environ.get('TEST_DATABASE_URL')
    if not url:
        pytest.skip('TEST_DATABASE_URL non configurata (database di test separato)')
    engine=create_engine(url.replace('postgresql://','postgresql+psycopg://'),poolclass=StaticPool,connect_args={'prepare_threshold':None})
    uid=uuid4()
    with Session(engine) as session:
        session.execute(text('INSERT INTO sb2_users(id,email,display_name) VALUES(:id,:email,\'Test\')'),{'id':uid,'email':str(uid)+'@test.local'})
        session.commit()
        monkeypatch.setattr(Repository,'user_id',lambda self:uid)
        monkeypatch.setattr(Repository,'today',lambda self:date(2026,11,15))
        yield session,uid
    engine.dispose()


def case_plan(session):
    case=planning.create_case(CaseInput(code=str(uuid4()),title='Pratica',context_markdown='Situazione da chiarire'),session)
    plan=planning.create_plan(PlanInput(case_id=case['id'],brief='Iniziare dal 2027'),session)
    return case,plan


def draft_plan(session,p):
    d=make_draft(target_copies=None,milestones=[])
    return planning.save_draft(p['id'],DraftInput(revision=p['revision'],draft=d),session)


def test_approval_clean_and_regeneration(db):
    s,uid=db
    c,p=case_plan(s)
    manual=planning.manual_task(c['id'],TaskCreate(title='Attività manuale'),s)
    p=draft_plan(s,p)
    assert s.execute(text('SELECT count(*) FROM sb2_tasks WHERE plan_id=:id'),{'id':p['id']}).scalar()==0
    p=planning.approve(p['id'],RevisionInput(revision=p['revision']),s)
    assert len(p['tasks'])==1
    again=planning.approve(p['id'],RevisionInput(revision=p['revision']-1),s)
    assert len(again['tasks'])==1
    planning.clean(p['id'],RevisionInput(revision=p['revision']),s)
    assert s.execute(text('SELECT status FROM sb2_tasks WHERE id=:id'),{'id':manual['id']}).scalar()=='open'
    assert planning.detail(p['id'],s)['tasks'][0]['status']=='cancelled'
    second=planning.create_plan(PlanInput(case_id=c['id'],brief='Nuovo piano'),s)
    second=draft_plan(s,second)
    second=planning.approve(second['id'],RevisionInput(revision=second['revision']),s)
    assert len(second['tasks'])==1


def test_completed_tasks_survive_clean(db):
    s,uid=db
    c,p=case_plan(s);p=draft_plan(s,p);p=planning.approve(p['id'],RevisionInput(revision=p['revision']),s)
    Repository(s).complete_task(p['tasks'][0]['id'])
    planning.clean(p['id'],RevisionInput(revision=p['revision']),s)
    kept=planning.detail(p['id'],s)['tasks'][0]
    assert kept['status']=='completed' and kept['completed_at']


def test_discard_and_conflict(db):
    s,uid=db
    c,p=case_plan(s);p=draft_plan(s,p)
    p=planning.discard(p['id'],RevisionInput(revision=p['revision']),s)
    assert not planning.detail(p['id'],s)['tasks']
    with pytest.raises(HTTPException) as error:
        planning.approve(p['id'],RevisionInput(revision=p['revision']),s)
    assert error.value.status_code==409
    s.rollback()


def test_interview_and_generate_do_not_create_tasks(db,monkeypatch):
    s,uid=db;c,p=case_plan(s)
    answers=iter([json.dumps({'text':'Quali documenti hai già raccolto?','ready':False}),make_draft(target_copies=None,milestones=[]).model_dump_json()])
    async def fake_complete(*args,**kwargs):return next(answers)
    monkeypatch.setattr(planning,'complete',fake_complete)
    p=asyncio.run(planning.interview(p['id'],TurnInput(text='Aiutami a chiarire',revision=p['revision']),s))
    assert len(p['dialogue'])==2
    p=asyncio.run(planning.generate(p['id'],RevisionInput(revision=p['revision']),s))
    assert p['status']=='draft' and not p['tasks']


def test_stale_revision_rejected(db):
    s,uid=db;c,p=case_plan(s);p=draft_plan(s,p)
    with pytest.raises(HTTPException) as error:
        planning.approve(p['id'],RevisionInput(revision=p['revision']-1),s)
    assert error.value.status_code==409
    s.rollback()


def test_contextual_overdue_not_automatically_completed(db):
    s,uid=db;c,p=case_plan(s)
    task=planning.manual_task(c['id'],TaskCreate(title='Da fare',due_date=date(2026,11,1),due_time='10:00'),s)
    event=planning.manual_event(c['id'],EventCreate(title='Appuntamento',event_date=date(2026,11,1),start_time='10:00'),s)
    apply_calendar_rules(s,uid,datetime(2026,11,15,12))
    assert s.execute(text('SELECT status FROM sb2_tasks WHERE id=:id'),{'id':task['id']}).scalar()=='planned'
    assert s.execute(text('SELECT status FROM sb2_events WHERE id=:id'),{'id':event['id']}).scalar()=='planned'


def test_book_monitor_correction_and_tree_clean(db):
    s,uid=db
    author=s.execute(text("INSERT INTO sb2_author_profiles(user_id,code,display_name) VALUES(:uid,'CESARE','Cesare') RETURNING id"),{'uid':uid}).scalar()
    book=s.execute(text("INSERT INTO sb2_books(author_profile_id,code,title,status) VALUES(:a,:code,'Libro test','draft') RETURNING id"),{'a':author,'code':str(uuid4())}).scalar();s.commit()
    p=planning.create_plan(PlanInput(book_id=book,brief='Q4 target 100'),s)
    p=planning.save_draft(p['id'],DraftInput(revision=p['revision'],draft=make_draft()),s)
    p=planning.approve(p['id'],RevisionInput(revision=p['revision']),s)
    assert planning.monitor(p['id'],s)['status']=='data_missing'
    s.execute(text("INSERT INTO sb2_sales(user_id,book_id,sale_date,quantity) VALUES(:uid,:book,'2026-11-05',28)"),{'uid':uid,'book':book});s.commit()
    state=planning.coverage(p['id'],CoverageInput(through=date(2026,11,8)),s)
    assert state['status']=='below_threshold' and state['deviation_percent']==-30
    child=planning.correction(p['id'],s)
    assert planning.correction(p['id'],s)['id']==child['id']
    child=planning.save_draft(child['id'],DraftInput(revision=child['revision'],draft=make_draft(target_copies=None,milestones=[])),s)
    child=planning.approve(child['id'],RevisionInput(revision=child['revision']),s)
    assert len(planning.detail(p['id'],s)['tasks'])==2
    planning.clean(p['id'],RevisionInput(revision=p['revision']),s)
    assert planning.detail(child['id'],s)['status']=='cleaned'
    assert all(t['status']=='cancelled' for t in planning.detail(p['id'],s)['tasks'])
    assert s.execute(text('SELECT SUM(quantity) FROM sb2_sales WHERE book_id=:id'),{'id':book}).scalar()==28


def test_case_ownership_checked(db):
    s,uid=db
    other=uuid4();s.execute(text("INSERT INTO sb2_users(id,email,display_name) VALUES(:id,:email,'Other')"),{'id':other,'email':str(other)+'@test.local'})
    case=s.execute(text("INSERT INTO sb2_cases(user_id,code,title,status) VALUES(:uid,'OTHER','Other','active') RETURNING id"),{'uid':other}).scalar();s.commit()
    with pytest.raises(HTTPException) as error:
        planning.manual_task(case,TaskCreate(title='Wrong owner'),s)
    assert error.value.status_code==404


def test_changed_context_requires_regeneration(db):
    s,uid=db;c,p=case_plan(s);p=draft_plan(s,p)
    planning.update_case(c['id'],CaseInput(code=c['code'],title='Nuova situazione',context_markdown='Dati cambiati'),s)
    with pytest.raises(HTTPException) as error:
        planning.approve(p['id'],RevisionInput(revision=p['revision']),s)
    assert error.value.status_code==409
    s.rollback()


def test_regenerate_keeps_context_and_no_calendar_writes(db):
    s,uid=db;c,p=case_plan(s);p=draft_plan(s,p)
    p=planning.discard(p['id'],RevisionInput(revision=p['revision']),s)
    new=planning.regenerate(p['id'],RevisionInput(revision=p['revision']),s)
    assert new['id']!=p['id'] and new['case_id']==c['id']
    assert new['status']=='interview' and not new['tasks'] and new['draft'] is None


def test_financial_events_are_scoped_and_read_only(db):
    s,uid=db
    account=s.execute(text("INSERT INTO sb2_accounts(user_id,code,display_name,account_type) VALUES(:uid,'TEST','Conto test','bank') RETURNING id"),{'uid':uid}).scalar()
    s.execute(text("INSERT INTO sb2_transactions(user_id,account_id,transaction_date,description,amount,status) VALUES(:uid,:account,'2026-11-05','Rata',-100,'planned'),(:uid,:account,'2026-11-06','Incasso',200,'confirmed')"),{'uid':uid,'account':account});s.commit()
    items=planning.financial_events(date(2026,11,1),date(2026,11,30),s)
    assert len(items)==1 and items[0]['description']=='Rata' and items[0]['amount']==-100
    assert s.execute(text('SELECT count(*) FROM sb2_events WHERE user_id=:uid'),{'uid':uid}).scalar()==0
    assert not planning.financial_events(date(2026,12,1),date(2026,12,31),s)


def test_case_proposal_confirmation_is_idempotent(db):
    s,uid=db
    repo=Repository(s)
    conv=repo.create_conversation('Test pratica')
    metadata={'result':{'kind':'case_proposal','data':{'title':'Contributi','context_markdown':'Situazione originale','questions':['Quali documenti?']}}}
    msg=repo.add_conversation_message(conv['id'],'assistant','Riepilogo','case_proposal',metadata)
    first=planning.confirm_case_proposal(msg['id'],s)
    second=planning.confirm_case_proposal(msg['id'],s)
    assert first['id']==second['id']
    assert s.execute(text('SELECT count(*) FROM sb2_cases WHERE user_id=:uid'),{'uid':uid}).scalar()==1
    assert s.execute(text('SELECT count(*) FROM sb2_tasks WHERE user_id=:uid'),{'uid':uid}).scalar()==0


def test_assistant_proposes_case_without_creating_it(db,monkeypatch):
    from app.assistant import answer
    s,uid=db
    async def fake(messages):return {'title':'Contributi','summary':'Verificare situazione','questions':['Quando vuoi iniziare?']}
    monkeypatch.setattr(planning,'model_json',fake)
    result=asyncio.run(answer(s,'Apri una nuova pratica per i contributi. Inizio nel 2027.'))
    assert result['kind']=='case_proposal'
    assert '2027' in result['data']['context_markdown']
    assert s.execute(text('SELECT count(*) FROM sb2_cases WHERE user_id=:uid'),{'uid':uid}).scalar()==0


def test_project_counts_include_approved_book_plan(db):
    s,uid=db
    repo=Repository(s)
    s.execute(text("INSERT INTO sb2_author_profiles(user_id,code,display_name) VALUES(:uid,'CESARE','Cesare')"),{'uid':uid});s.commit()
    project=repo.create_project({'code':'BOOK_'+uuid4().hex[:12],'title':'Nuovo libro','kind':'book','author_code':'CESARE','publication_date':None,'objective':'Lancio'})
    p=planning.create_plan(PlanInput(book_id=project['book_id'],brief='Target 100'),s)
    p=planning.save_draft(p['id'],DraftInput(revision=p['revision'],draft=make_draft()),s)
    planning.approve(p['id'],RevisionInput(revision=p['revision']),s)
    items=repo.projects()
    assert len(items[0]['tasks'])==1 and items[0]['book_id']==project['book_id']


def test_inventory_purchase_sale_and_delete(db):
    s,uid=db
    author=s.execute(text("INSERT INTO sb2_author_profiles(user_id,code,display_name) VALUES(:uid,:code,'Flavio') RETURNING id"),{'uid':uid,'code':str(uuid4())}).scalar()
    code=str(uuid4())
    s.execute(text("INSERT INTO sb2_books(author_profile_id,code,title,status) VALUES(:a,:code,'Gabriella','draft')"),{'a':author,'code':code});s.commit()
    planning.purchase_stock(planning.StockPurchase(book_code=code,quantity=30,purchase_date=date(2026,11,1)),s)
    repo=Repository(s)
    data={'book_code':code,'format_code':'paperback','quantity':7,'sale_date':date(2026,11,2),'channel':'Evento','notes':None,'from_inventory':True}
    repo.add_sale(data)
    repo.add_sale({**data,'quantity':5,'from_inventory':False})
    item=planning.inventory(s)['items'][0]
    assert item['available']==23 and item['sold']==7 and item['purchased']==30
    assert repo.sales_progress()['items'][0]['sold']==12
    with pytest.raises(ValueError): repo.add_sale({**data,'quantity':24})
    s.rollback()
    with pytest.raises(ValueError): repo.add_sale({**data,'format_code':'ebook'})
    s.rollback()
    purchase=planning.inventory(s)['purchases'][0]
    with pytest.raises(HTTPException): planning.delete_stock(purchase['id'],s)
    s.rollback()
    sale=next(x for x in repo.sales_progress()['recent_sales'] if x['from_inventory'])
    repo.delete_sale(sale['id'])
    assert planning.inventory(s)['items'][0]['available']==30
    planning.delete_stock(purchase['id'],s)
    assert planning.inventory(s)['items'][0]['available']==0
