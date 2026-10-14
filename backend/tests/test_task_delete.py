from uuid import uuid4
import pytest
from app.repository import Repository

class Session:
    def __init__(self,found):self.found=found;self.queries=[];self.commits=0
    def execute(self,query,args):
        assert args['uid']=='owner'
        self.queries.append(str(query));return self
    def mappings(self):return self
    def one_or_none(self):return self.found
    def commit(self):self.commits+=1

def repository(session):
    repo=Repository(session)
    repo.user_id=lambda:'owner'
    repo.log=lambda *args:setattr(session,'logged',args)
    return repo

def test_deleted_task_is_cancelled_and_scoped_to_owner():
    identity=uuid4()
    session=Session({'id':identity,'status':'open','project_id':uuid4()})
    repository(session).delete_task(identity)
    assert session.commits==1
    assert "status='cancelled'" in session.queries[-1]
    assert all('user_id=:uid' in q for q in session.queries)
    assert session.logged[3]=='delete'
    assert not any('UPDATE sb2_projects' in q or 'DELETE FROM' in q for q in session.queries)

def test_missing_or_other_users_task_is_not_changed():
    session=Session(None)
    with pytest.raises(KeyError):repository(session).delete_task(uuid4())
    assert session.commits==0 and len(session.queries)==1

def test_completed_task_can_be_deleted_without_becoming_open():
    identity=uuid4()
    session=Session({'id':identity,'status':'completed','completed_at':'2026-10-12'})
    repository(session).delete_task(identity)
    assert "status<>'cancelled'" in session.queries[0]
    assert "status='cancelled'" in session.queries[1]
    assert session.logged[4]['status']=='completed'
    assert session.commits==1

def test_completed_past_list_is_scoped_filtered_and_recent_first():
    class Reads(Session):
        def all(self):return []
    session=Reads(None)
    repo=repository(session)
    repo.today=lambda:'2026-10-14'
    assert repo.completed_past_tasks()==[]
    query=session.queries[0]
    assert "status='completed'" in query and 'due_date<:today' in query
    assert 'due_date DESC' in query and 'user_id=:uid' in query
    assert session.commits==0

def test_false_completion_is_recorded_as_explicit_correction():
    identity=uuid4()
    session=Session({'id':identity,'status':'completed','title':'Pubblicato libro','book_id':'book'})
    repository(session).delete_task(identity,incorrect_information=True,reason=' Il libro non è stato pubblicato ')
    correction=session.logged[5]
    assert correction['incorrect_information'] is True
    assert correction['invalidates_completion_evidence'] is True
    assert correction['reason']=='Il libro non è stato pubblicato'
    assert session.logged[4]['title']=='Pubblicato libro'
