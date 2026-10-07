import asyncio
from uuid import uuid4
import pytest
from fastapi import HTTPException
from app import work
from app import assistant

class Repo:
    def __init__(self, session): pass
    def user_id(self): return uuid4()

@pytest.mark.parametrize('prompt',['quante strategie attive ci sono?','uante strategie attive ci sono?','quali strategie attive?'])
def test_strategy_question_reads_actual_counts(monkeypatch,prompt):
    monkeypatch.setattr(assistant,'Repository',Repo)
    monkeypatch.setattr(work,'overview',lambda s:{'strategies_active':2,'plans_active':1,'cards':[{'strategies':[{'title':'Peter'},{'title':'Rubicone'}]}]})
    result=asyncio.run(assistant.answer(None,prompt))
    assert result['mode']=='deterministic'
    assert 'attive: 2' in result['message'] and 'Peter' in result['message']

def test_dedicated_assistant_contains_source_and_never_calls_general_actions(monkeypatch):
    identity=uuid4()
    monkeypatch.setattr(work,'context',lambda *a:{'title':'Libro','synopsis':'Contesto reale'})
    monkeypatch.setattr(work,'overview',lambda s:{'cards':[]})
    class R(Repo):
        def today(self):return '2026-10-07'
    monkeypatch.setattr(work,'Repository',R)
    async def fake(messages, **kwargs):
        assert 'Contesto reale' in messages[0]['content']
        assert 'non eseguire operazioni' in messages[0]['content']
        assert messages[-1]['content']=='Crea una attività'
        return '{"text":"Proposta da approvare","actions":[]}' 
    monkeypatch.setattr(work,'complete',fake)
    result=asyncio.run(work.scoped_answer(None,{'book_id':identity,'case_id':None},'Crea una attività',[]))
    assert result['message']=='Proposta da approvare'

@pytest.mark.parametrize('status,confirm',[('active',True),('closed',False)])
def test_delete_requires_closed_case_and_confirmation(monkeypatch,status,confirm):
    monkeypatch.setattr(work,'context',lambda *a:{'status':status})
    monkeypatch.setattr(work,'Repository',Repo)
    with pytest.raises(HTTPException) as exc:work.delete_case(uuid4(),confirm,None)
    assert exc.value.status_code==409

def test_proposed_event_without_date_is_not_written(monkeypatch):
    import json
    identity=uuid4()
    monkeypatch.setattr(work,'context',lambda *a:{'title':'Fruit','status':'active'})
    monkeypatch.setattr(work,'Repository',Repo)
    class Session:
        def execute(self, sql, args):
            assert not str(sql).startswith('INSERT')
            return self
        def mappings(self):return self
        def one_or_none(self):return {'case_id':identity,'book_id':None,'status':'active','metadata_json':json.dumps({'result':{'data':{'actions':[{'kind':'event','title':'Test'}]}}})}
    with pytest.raises(HTTPException) as exc:
        work.confirm_actions(uuid4(),work.ActionApproval(actions=[work.WorkAction(kind='event',title='Test')]),Session())
    assert exc.value.status_code==422

def test_repeated_confirmation_returns_saved_result_without_inserts(monkeypatch):
    import json
    monkeypatch.setattr(work,'Repository',Repo)
    class Session:
        def execute(self,sql,args):
            assert not str(sql).startswith('INSERT')
            return self
        def mappings(self):return self
        def one_or_none(self):return {'metadata_json':json.dumps({'result':{'data':{'applied':True,'created':[{'id':'already-created'}]}}})}
    result=work.confirm_actions(uuid4(),work.ActionApproval(actions=[work.WorkAction(kind='task',title='Test')]),Session())
    assert result['created'][0]['id']=='already-created'

def test_confirmation_inserts_event_with_case_id_and_commits_once(monkeypatch):
    import json
    from datetime import date
    identity=uuid4();created=uuid4()
    class R(Repo):
        def log(self,*args):pass
    monkeypatch.setattr(work,'Repository',R)
    monkeypatch.setattr(work,'context',lambda *a:{'title':'Fruit','status':'active'})
    class Session:
        commits=0
        inserts=[]
        def execute(self,sql,args):
            if str(sql).startswith('INSERT'):
                self.inserts.append(args.copy())
            return self
        def mappings(self):return self
        def one_or_none(self):return {'case_id':identity,'book_id':None,'status':'active','metadata_json':json.dumps({'result':{'data':{'actions':[{'kind':'event','title':'Test'}]}}})}
        def scalar_one(self):return created
        def commit(self):self.commits+=1
    session=Session()
    result=work.confirm_actions(uuid4(),work.ActionApproval(actions=[work.WorkAction(kind='event',title='Test',date=date(2026,10,8))]),session)
    assert result['applied'] and session.commits==1
    assert session.inserts[0]['case_id']==identity and session.inserts[0]['book_id'] is None
