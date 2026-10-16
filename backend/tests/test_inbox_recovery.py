import asyncio
import json
import pytest
from fastapi import HTTPException
from app import inbox

class Session:
    def __init__(self):self.queries=[];self.commits=0;self.rollbacks=0
    def execute(self,query,args):
        assert args['uid']=='owner'
        self.queries.append(str(query));return self
    def scalar_one_or_none(self):return 'claimed'
    def commit(self):self.commits+=1
    def rollback(self):self.rollbacks+=1

class Repo:
    def __init__(self,session):self.session=session
    def user_id(self):return 'owner'
    def set_inbox_error(self,identity,error):self.session.error=(identity,error);return {'id':identity}
    def create_conversation(self,title):return {'id':'chat'}
    def add_conversation_message(self,*args):
        self.session.messages=getattr(self.session,'messages',[])+[args]
    def complete_inbox(self,identity,result):self.session.resolved=(identity,result)
    def add_inbox(self,*args):raise AssertionError('Retry must not duplicate inbox rows')

@pytest.fixture
def setup(monkeypatch):
    row={'id':'item','text':'Scrivi una bozza','status':'new','source':'llm_failed','interpretation_json':None}
    monkeypatch.setattr(inbox,'Repository',Repo)
    monkeypatch.setattr(inbox,'owned',lambda *args:row)
    return row

def test_failed_retry_reuses_original_without_archiving_or_duplicating(monkeypatch,setup):
    async def answer(session,prompt,**kwargs):
        item=kwargs['failure_sink']('Quota temporaneamente esaurita')
        assert item['id']=='item'
        return {'mode':'queued','kind':'inbox','message':'Quota temporaneamente esaurita'}
    monkeypatch.setattr(inbox,'answer',answer)
    session=Session()
    result=asyncio.run(inbox.retry_inbox('item',session))
    assert not result['resolved'] and session.error[0]=='item'
    assert not hasattr(session,'resolved') and not hasattr(session,'messages')
    assert "AND status='new' RETURNING id" in session.queries[0]

def test_article_retry_preserves_full_content_and_copy_metadata(monkeypatch,setup):
    article={'title':'Oggetto','content_markdown':'Corpo completo della mailing list','author_code':'FLAVIO','content_format':'email'}
    async def answer(*args,**kwargs):return {'mode':'llm','kind':'article','data':article}
    monkeypatch.setattr(inbox,'answer',answer)
    session=Session();result=asyncio.run(inbox.retry_inbox('item',session))
    assert result['resolved'] and result['conversation_id']=='chat'
    assert session.messages[-1][2]=='Corpo completo della mailing list'
    assert session.messages[-1][3:] == ('article',article)
    assert session.resolved[1]['conversation_id']=='chat'

def test_note_does_not_retry_or_create_operations(monkeypatch,setup):
    setup['source']='desktop'
    session=Session()
    with pytest.raises(HTTPException) as exc:asyncio.run(inbox.retry_inbox('item',session))
    assert exc.value.status_code==409 and not session.queries

def test_archived_request_cannot_run_twice(monkeypatch,setup):
    setup['status']='confirmed'
    session=Session()
    with pytest.raises(HTTPException) as exc:asyncio.run(inbox.retry_inbox('item',session))
    assert exc.value.status_code==409 and not session.queries

def test_produced_result_is_archived_if_chat_storage_fails(monkeypatch,setup):
    class Broken(Repo):
        def create_conversation(self,title):raise RuntimeError('chat unavailable')
    monkeypatch.setattr(inbox,'Repository',Broken)
    async def answer(*args,**kwargs):return {'mode':'llm','kind':'task_created','message':'Attività creata','data':{'id':'task'}}
    monkeypatch.setattr(inbox,'answer',answer)
    session=Session()
    with pytest.raises(RuntimeError):asyncio.run(inbox.retry_inbox('item',session))
    assert session.resolved[1]['result']['kind']=='task_created'
    assert not hasattr(session,'error') # Not requeued for duplicate execution.

def test_edit_preserves_error_and_only_stores_context_references(monkeypatch,setup):
    setup['interpretation_json']=json.dumps({'last_error':'Timeout'})
    session=Session()
    inbox.edit('item',inbox.InboxUpdate(text='Appunto corretto',category='note'),session)
    assert session.commits==1
    assert all('sb2_projects SET' not in query and 'sb2_tasks' not in query for query in session.queries)
