from uuid import uuid4
import pytest
from fastapi import HTTPException
from app import strategic as s

class Repo:
    def __init__(self,session):self.session=session
    def user_id(self):return 'owner'
    def log(self,*args):self.session.log=args

class Session:
    def __init__(self,found):self.found=found;self.queries=[];self.commits=0
    def execute(self,query,args):
        assert args['uid']=='owner'
        self.queries.append(str(query))
        return self
    def mappings(self):return self
    def one_or_none(self):return self.found
    def commit(self):self.commits+=1

def test_delete_only_owned_diary_message_without_deleting_conversation_or_projects(monkeypatch):
    monkeypatch.setattr(s,'Repository',Repo)
    identity=uuid4();cid=uuid4()
    session=Session({'id':identity,'conversation_id':cid})
    s.delete_diary_entry(identity,session)
    assert session.commits==1
    deletion=session.queries[-1]
    assert 'c.user_id=:uid' in deletion and "m.role='user'" in deletion
    assert "m.message_kind='strategic_diary'" in deletion
    assert 'm.id=:id' in deletion
    assert not any('DELETE FROM sb2_conversations' in q or 'sb2_tasks' in q or 'sb2_projects' in q for q in session.queries)
    assert session.log[1:4]==('diary_entry',identity,'delete')

def test_unowned_or_non_diary_message_is_not_deleted(monkeypatch):
    monkeypatch.setattr(s,'Repository',Repo)
    session=Session(None)
    with pytest.raises(HTTPException) as exc:s.delete_diary_entry(uuid4(),session)
    assert exc.value.status_code==404 and session.commits==0
