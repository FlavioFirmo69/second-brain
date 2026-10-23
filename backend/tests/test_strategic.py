import asyncio
import json
from contextlib import nullcontext
from uuid import uuid4
from datetime import date
from types import SimpleNamespace
import pytest
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from app import strategic as s

class Repo:
    settings = SimpleNamespace(app_timezone='Europe/Rome')
    def __init__(self, session): self.session = session
    def user_id(self): return 'owner'
    def today(self): return '2026-10-14'
    def create_conversation(self, title): return {'id': uuid4()}
    def add_conversation_message(self, *args): pass

class Session:
    def __init__(self): self.sql = []; self.committed = False
    def begin_nested(self): return nullcontext()
    def execute(self, query, args):
        self.sql.append(str(query)); assert args.get('uid') == 'owner'
        return self
    def scalar_one(self): return uuid4()
    def commit(self): self.committed = True

@pytest.fixture
def context(monkeypatch):
    monkeypatch.setattr(s, 'Repository', Repo)
    data = {'sources': {
        'projects': [{'id': 'sigma', 'title': 'Sigma', 'objective': 'Consulenza organizzativa AI'}],
        'cases': [{'id': 'fruit', 'title': 'Fruit', 'context_markdown': 'Offerta commerciale solo dopo validazione tecnica'}],
        'plans': [{'id': 'plan', 'case_id': 'fruit', 'draft': {'condition': 'Validazione tecnica prima dell’offerta'}}],
        'author_profiles': [{'id': 'writer', 'positioning': 'Scrittore indipendente; autonomia creativa'}],
        'events': [{'id': 'work', 'title': 'Lavoro dipendente', 'start_time': '09:00', 'end_time': '18:00'}]},
        'unavailable': [], 'date': '2026-10-14'}
    monkeypatch.setattr(s, 'official_context', lambda session: data)
    monkeypatch.setattr(s, 'memories', lambda session: [])
    monkeypatch.setattr(s, 'diary_context', lambda session: {'entries':[], 'note':'Testimony'})
    return data

@pytest.mark.parametrize('prompt,expected', [
    ('Novità Sigma: chiedono più giornate', 'Consulenza organizzativa AI'),
    ('Fruit vuole anticipare l’offerta', 'Validazione tecnica prima'),
    ('Accetto straordinari nel lavoro dipendente?', '18:00'),
    ('Scelgo una consulenza più impegnativa?', 'Scrittore indipendente')])
def test_advice_retrieves_official_and_personal_context(monkeypatch, context, prompt, expected):
    async def complete(messages, **kwargs):
        if 'Estrai selettivamente' in messages[0]['content']:
            return '{"candidates":[]}'
        data = messages[-2]['content']
        assert expected in data and 'autonomia creativa' in data
        assert 'costo-opportunità' in messages[0]['content']
        assert 'Distingui fatti' in messages[0]['content']
        return 'Valutazione di prova'
    monkeypatch.setattr(s, 'complete', complete)
    session = Session()
    result = asyncio.run(s.advice(s.Question(text=prompt), session))
    assert result['message'] == 'Valutazione di prova'
    assert not session.sql  # No task/event/project/memory mutation.

def test_cross_domain_memory_keeps_reference_without_project_snapshot(monkeypatch, context):
    async def complete(messages, **kwargs):
        candidate = json.loads(messages[-1]['content'])['candidate']
        assert candidate['source_refs'] == ['projects:sigma']
        assert 'status' not in candidate
        return '{"accept":true,"reason":"Decisione trasversale durevole"}'
    monkeypatch.setattr(s, 'complete', complete)
    session = Session()
    asyncio.run(s.save_memory(s.Memory(kind='constraint',content='Proteggere due serate settimanali per la scrittura',rationale='Preservare autonomia e continuità creativa',source_refs=['projects:sigma']),session))
    assert session.committed
    assert sum('INSERT' in q for q in session.sql) == 1
    assert 'sb2_strategic_memories' in session.sql[-1]

@pytest.mark.parametrize('verdict', [
    '{"accept":false,"reason":"Informazione occasionale"}',
    '{"accept":false,"reason":"Dato ufficiale già rappresentato"}',
    '{"accept":false,"reason":"Duplicato semantico"}',
    'invalid JSON'])
def test_ineligible_memory_never_persists(monkeypatch,context,verdict):
    async def complete(*args, **kwargs): return verdict
    monkeypatch.setattr(s, 'complete', complete)
    session = Session()
    with pytest.raises(HTTPException):
        asyncio.run(s.save_memory(s.Memory(kind='learning',content='Oggi ho incontrato un collega al bar',rationale='Una informazione ricevuta questa mattina'),session))
    assert not session.committed and not any('INSERT' in q for q in session.sql)

def test_missing_source_is_reported_and_blocks_memory(monkeypatch,context):
    context['unavailable'] = ['plans']
    async def complete(*args, **kwargs): return 'Consiglio limitato'
    monkeypatch.setattr(s, 'complete', complete)
    result = asyncio.run(s.advice(s.Question(text='Novità Fruit'),Session()))
    assert 'Fonti non accessibili: plans' in result['message']
    with pytest.raises(HTTPException) as exc:
        asyncio.run(s.save_memory(s.Memory(kind='decision',content='Proteggere il tempo personale',rationale='Vincolo utile a più progetti'),Session()))
    assert exc.value.status_code == 503

def test_official_queries_are_scoped_and_read_only(monkeypatch):
    monkeypatch.setattr(s, 'Repository', Repo)
    class Reads(Session):
        def mappings(self): return self
        def all(self): return []
    session = Reads()
    result = s.official_context(session)
    assert set(result['sources']) == set(s.SOURCES)
    assert all(q.startswith('SELECT') and ':uid' in q for q in session.sql)

def test_source_failure_recovers_with_savepoint(monkeypatch):
    monkeypatch.setattr(s, 'Repository', Repo)
    class Reads(Session):
        def execute(self,q,args):
            super().execute(q,args)
            if 'sb2_plans' in str(q): raise SQLAlchemyError('unavailable')
            return self
        def mappings(self):return self
        def all(self):return []
    result = s.official_context(Reads())
    assert result['unavailable'] == ['plans']
    assert 'author_profiles' in result['sources']

def diary_candidate(quote):
    return {'kind':'learning', 'content':'Episodio HR: mantenere confini espliciti ha aiutato a evitare coinvolgimento AI; condotta coerente con la priorità di restare ai margini.',
            'rationale':'Apprendimento utile nelle future richieste di coinvolgimento lavorativo',
            'source_refs':['projects:sigma'], 'evidence_quotes':[quote]}

def test_mixed_diary_extracts_grounded_learning_and_ignores_noise(monkeypatch,context):
    quote = 'ho parlato con HR del progetto AI e sono riuscito a non farmi coinvolgere'
    current = 'Oggi '+quote+'. Ho bevuto un caffè e comprato il pane.'
    context['sources']['projects'][0]['objective'] += '; restare ai margini del lavoro dipendente'
    calls = []
    async def complete(messages, **kwargs):
        calls.append(messages)
        if 'Estrai selettivamente' in messages[0]['content']:
            assert 'restare ai margini' in messages[-1]['content']
            return json.dumps({'candidates':[diary_candidate(quote)]})
        payload = json.loads(messages[-1]['content'])
        assert payload['diary_evidence']['quotes'] == [quote]
        assert 'Evidenza riferita dall’utente (2026-10-14)' in payload['candidate']['rationale']
        assert 'pane' not in payload['candidate']['content']
        return '{"accept":true,"reason":"Apprendimento sostenuto dal racconto"}'
    monkeypatch.setattr(s,'complete',complete)
    session = Session()
    result = asyncio.run(s.extract_memories(session,current,[]))
    assert len(result['saved']) == 1 and len(calls) == 2
    assert not result['unavailable']
    assert all('sb2_strategic_memories' in q for q in session.sql if 'INSERT' in q)

@pytest.mark.parametrize('quote', ['HR ha escluso definitivamente ogni incarico', 'un vecchio episodio'])
def test_fabricated_or_history_only_evidence_is_not_saved(monkeypatch,context,quote):
    async def complete(*args,**kwargs):
        return json.dumps({'candidates':[diary_candidate(quote)]})
    monkeypatch.setattr(s,'complete',complete)
    session = Session()
    result = asyncio.run(s.extract_memories(session,'Oggi ho bevuto un caffè',[{'role':'user','content':'un vecchio episodio'}]))
    assert not result['saved'] and not session.sql

def test_authentic_quote_does_not_bypass_semantic_validation(monkeypatch,context):
    current = 'Ho parlato con HR del progetto AI'
    async def complete(messages,**kwargs):
        if 'Estrai selettivamente' in messages[0]['content']:
            candidate = diary_candidate(current)
            candidate['content'] = 'L’utente desidera sempre restare ai margini del lavoro dipendente'
            return json.dumps({'candidates':[candidate]})
        return '{"accept":false,"reason":"Preferenza non documentata"}'
    monkeypatch.setattr(s,'complete',complete)
    session = Session()
    result = asyncio.run(s.extract_memories(session,current,[]))
    assert not result['saved'] and not any('INSERT' in q for q in session.sql)

def test_casual_diary_has_no_permanent_memory(monkeypatch,context):
    async def complete(*args,**kwargs):return '{"candidates":[]}'
    monkeypatch.setattr(s,'complete',complete)
    session = Session()
    result = asyncio.run(s.extract_memories(session,'Oggi piove, ho preso un caffè e comprato il pane',[]))
    assert result == {'saved':[], 'unavailable':False}
    assert not session.sql

def test_extractor_failure_retains_diary_and_reports_no_saved_memory(monkeypatch,context):
    saved_messages = []
    class R(Repo):
        def add_conversation_message(self,*args):saved_messages.append(args)
    monkeypatch.setattr(s,'Repository',R)
    async def complete(messages,**kwargs):
        if 'Estrai selettivamente' in messages[0]['content']:
            raise s.LlmUnavailable('offline')
        return 'Consiglio concreto'
    monkeypatch.setattr(s,'complete',complete)
    result = asyncio.run(s.advice(s.Question(text='Racconto della giornata',mode='diary'),Session()))
    assert result['memory']['unavailable']
    assert saved_messages[0][1:3] == ('user','Racconto della giornata')
    assert 'non è stata completata' in result['message']


def test_dated_suggestion_is_stored_on_assistant_message_and_returned_for_buttons(monkeypatch,context):
    context['sources']['strategies']=[{'id':'cesare','status':'active','content_markdown':'Lettori responsabili commerciali PMI'}]
    logged=[]
    class R(Repo):
        def add_conversation_message(self,*args):
            logged.append(args)
            return {'id':str(uuid4()),'role':args[1],'content_markdown':args[2],
                    'message_kind':args[3],'metadata':args[4] if len(args)>4 else None}
    monkeypatch.setattr(s,'Repository',R)
    async def complete(messages,**kwargs):
        assert kwargs['response_format']=={'type':'json_object'}
        assert 'La data è un obiettivo' in messages[0]['content']
        return json.dumps({'answer':'Possibile interlocutore, da verificare.', 'proposals':[{
            'action':'Sondare con Maurizio l’interesse per Cesare', 'proposed_date':'2026-10-30',
            'rationale':'Primo contatto indicativo, da concordare.', 'source_refs':['strategies:cesare']}]})
    monkeypatch.setattr(s,'complete',complete)
    result=asyncio.run(s.advice(s.Question(text='Quando potrei sondare Maurizio?'),Session()))
    assert result['message']=='Possibile interlocutore, da verificare.'
    assert result['assistant_message']['id']
    saved=result['assistant_message']['metadata']['strategic_proposals']
    assert saved[0]['status']=='proposed' and saved[0]['proposed_date']=='2026-10-30'
    assert logged[-1][4]['strategic_proposals']==saved
    assert logged[0][3]=='strategic_question' # No accepted decision is fabricated.


def test_new_diary_response_sees_previous_rejection_from_other_conversations(monkeypatch,context):
    rejection='Proposta strategica rifiutata: preferisco parlarne ad Arona, senza contatti prima.'
    monkeypatch.setattr(s,'diary_context',lambda session:{'entries':[{'content_markdown':rejection}]})
    async def complete(messages,**kwargs):
        if 'Estrai selettivamente' in messages[0]['content']:return '{"candidates":[]}'
        assert rejection in messages[-2]['content']
        return 'Tengo conto della decisione precedente.'
    monkeypatch.setattr(s,'complete',complete)
    result=asyncio.run(s.advice(s.Question(text='Maurizio sarà ad Arona.',mode='diary'),Session()))
    assert not result['error']

def test_editable_personal_document_is_used_for_hr_interpretation(monkeypatch,context):
    context['sources']['personal_profiles']=[{'id':'personal','revision':3,
        'content_markdown':'Nel lavoro dipendente desidero rimanere ai margini. Proteggere il tempo per la scrittura.'}]
    async def complete(messages,**kwargs):
        if 'Estrai selettivamente' in messages[0]['content']:
            return '{"candidates":[]}'
        assert 'desidero rimanere ai margini' in messages[-2]['content']
        assert 'versione corrente prevale sui vecchi ricordi' in messages[0]['content']
        return 'La condotta raccontata è coerente con il tuo profilo corrente.'
    monkeypatch.setattr(s,'complete',complete)
    result=asyncio.run(s.advice(s.Question(text='Ho parlato con HR del progetto AI e ho evitato il coinvolgimento.'),Session()))
    assert 'coerente con il tuo profilo' in result['message']

@pytest.mark.parametrize('mode,kind,expected',[
    ('diary','strategic_diary','breve riscontro'),
    ('advice','strategic_question','consiglio strategico complessivo')])
def test_diary_and_advice_intents_are_explicit(monkeypatch,context,mode,kind,expected):
    logged=[]
    class R(Repo):
        def add_conversation_message(self,*args):logged.append(args)
    monkeypatch.setattr(s,'Repository',R)
    async def complete(messages,**kwargs):
        if 'Estrai selettivamente' in messages[0]['content']:return '{"candidates":[]}'
        assert expected in messages[0]['content']
        return 'Risposta'
    monkeypatch.setattr(s,'complete',complete)
    asyncio.run(s.advice(s.Question(text='Ho evitato un coinvolgimento con HR',mode=mode),Session()))
    assert logged[0][3]==kind

def test_diary_is_scoped_searchable_paginated_and_excludes_advice_questions(monkeypatch):
    monkeypatch.setattr(s,'Repository',Repo)
    class Diary(Session):
        def execute(self,query,args):
            super().execute(query,args)
            self.args=args
            return self
        def scalar_one(self):return 2
        def mappings(self):return self
        def all(self):return [{'id':'entry','content_markdown':'Fatto HR'}]
    session=Diary()
    result=s.read_diary(start=date(2026,10,1),end=date(2026,10,14),search='HR_100%',offset=30,limit=30,session=session)
    assert result['total']==2 and result['offset']==30
    assert session.args['search']=='%HR\\_100\\%%'
    assert session.args['timezone']=='Europe/Rome'
    assert all('c.user_id=:uid' in query and "m.role='user'" in query for query in session.sql)
    assert all("m.message_kind='strategic_diary'" in query for query in session.sql)
    assert "m.message_kind='strategic_question'" not in session.sql[-1]
    assert 'LIMIT :limit OFFSET :offset' in session.sql[-1]

def test_invalid_diary_date_range_is_rejected_before_query():
    session=Session()
    with pytest.raises(HTTPException) as exc:
        s.read_diary(start=date(2026,10,14),end=date(2026,10,1),search='',offset=0,limit=30,session=session)
    assert exc.value.status_code==422 and not session.sql

def test_advice_about_old_diary_episode_fetches_original_even_outside_recent_history(monkeypatch,context):
    cid=uuid4();mid=uuid4()
    class R(Repo):
        def conversation_messages(self,*args):
            return [{'role':'user','content_markdown':'Messaggio recente'}]*40
    monkeypatch.setattr(s,'Repository',R)
    class Focus(Session):
        def mappings(self):return self
        def one_or_none(self):return {'id':mid,'conversation_id':cid,'content_markdown':'Episodio originale HR completo','created_at':'2026-10-01'}
        def scalar_one_or_none(self):return cid
    async def complete(messages,**kwargs):
        if 'Estrai selettivamente' in messages[0]['content']:return '{"candidates":[]}'
        data=json.loads(messages[-2]['content'].split('\n',1)[1])
        assert data['diary_episode_requested']['content_markdown']=='Episodio originale HR completo'
        assert len(messages)==33
        return 'Consiglio sull’episodio originale'
    monkeypatch.setattr(s,'complete',complete)
    result=asyncio.run(s.advice(s.Question(text='Che consiglio mi dai?',conversation_id=cid,diary_entry_id=mid),Focus()))
    assert result['conversation_id']==cid

def test_diary_episode_from_another_user_is_not_accessible(monkeypatch,context):
    class Missing(Session):
        def mappings(self):return self
        def one_or_none(self):return None
    session=Missing()
    with pytest.raises(HTTPException) as exc:
        asyncio.run(s.advice(s.Question(text='Consiglio',diary_entry_id=uuid4()),session))
    assert exc.value.status_code==404
    assert 'c.user_id=:uid' in session.sql[0]

def test_failed_advice_preserves_question_and_does_not_retry_for_memory(monkeypatch,context):
    logged=[]
    class R(Repo):
        def add_conversation_message(self,*args):logged.append(args)
    monkeypatch.setattr(s,'Repository',R)
    calls=[]
    async def complete(*args,**kwargs):
        calls.append(args)
        raise s.LlmUnavailable('Quota esaurita',code='rate_limit',status=429)
    async def forbidden(*args,**kwargs):raise AssertionError('Memory must not retry failed provider')
    monkeypatch.setattr(s,'complete',complete)
    monkeypatch.setattr(s,'extract_memories',forbidden)
    result=asyncio.run(s.advice(s.Question(text='Chiedo consiglio'),Session()))
    assert 'Quota esaurita' in result['message']
    assert result['error']=={'code':'rate_limit','status':429}
    assert result['memory']['skipped'] and len(calls)==1
    assert 'selezione della memoria non è stata completata' not in result['message']
    assert logged[0][1:3]==('user','Chiedo consiglio')

def test_global_advice_uses_cross_conversation_diary_and_does_not_extract_memory(monkeypatch,context):
    monkeypatch.setattr(s,'diary_context',lambda session:{'entries':[
        {'id':'day1','content_markdown':'Fruit: sviluppi futuri solo con accordo concreto'},
        {'id':'day2','content_markdown':'Lavoro: autonomia e tempo personale'}]})
    async def complete(messages,**kwargs):
        assert 'consiglio strategico complessivo' in messages[0]['content']
        assert 'non limitare il consiglio a quel singolo episodio' in messages[0]['content']
        data=json.loads(messages[-2]['content'].split('\n',1)[1])
        assert len(data['recent_diary']['entries'])==2
        assert 'author_profiles' in data['sources'] and 'projects' in data['sources']
        return 'Mantieni il perimetro di Fruit e proteggi il tempo per la scrittura.'
    async def forbidden(*args,**kwargs):raise AssertionError('Advice must not create memories')
    monkeypatch.setattr(s,'complete',complete)
    monkeypatch.setattr(s,'extract_memories',forbidden)
    result=asyncio.run(s.advice(s.Question(text='Valuta le attività rispetto al mio profilo'),Session()))
    assert result['memory']['skipped']
    assert 'proteggi il tempo' in result['message']

def test_deleted_false_publication_is_in_advice_context_and_overrides_old_diary(monkeypatch,context):
    correction=s.task_deletion_context({'id':'log','task_id':'task','created_at':'2026-10-14',
        'before_json':json.dumps({'title':'Pubblicato libro','status':'completed','book_id':'book'}),
        'after_json':json.dumps({'incorrect_information':True,'reason':'Il libro non è stato pubblicato'})})
    context['sources']['task_deletions']=[correction]
    monkeypatch.setattr(s,'diary_context',lambda session:{'entries':[{'content_markdown':'Il libro è stato pubblicato'}]})
    async def complete(messages,**kwargs):
        assert 'non è più\nuna prova' in messages[0]['content']
        assert 'prevale sulle vecchie affermazioni' in messages[0]['content']
        data=json.loads(messages[-2]['content'].split('\n',1)[1])
        assert data['sources']['task_deletions'][0]['incorrect_information'] is True
        assert data['sources']['task_deletions'][0]['book_id']=='book'
        return 'La precedente indicazione di pubblicazione è stata smentita.'
    monkeypatch.setattr(s,'complete',complete)
    result=asyncio.run(s.advice(s.Question(text='Valuta le mie attività'),Session()))
    assert 'smentita' in result['message']
