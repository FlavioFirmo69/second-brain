import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from app import personal_profile as p

class Result:
    def __init__(self,value):self.value=value
    def mappings(self):return self
    def one(self):return self.value
    def one_or_none(self):return self.value

class Session:
    def __init__(self,before=None):self.before=before;self.queries=[];self.commits=0
    def execute(self,sql,args):
        assert args['uid']=='owner'
        self.queries.append(str(sql))
        if str(sql).startswith('SELECT id,content'):return Result(self.before)
        if str(sql).startswith(('INSERT','UPDATE')):
            return Result({'id':'profile','content_markdown':args['content'],
                           'revision':self.before['revision']+1 if self.before else 1,'updated_at':'now'})
        return Result(None)
    def commit(self):self.commits+=1

class Repo:
    def __init__(self,session):self.session=session
    def user_id(self):return 'owner'
    def log(self,*args):self.session.logged=args

@pytest.fixture(autouse=True)
def repository(monkeypatch):monkeypatch.setattr(p,'Repository',Repo)

def test_unconfigured_profile_shows_template_without_saving():
    session=Session()
    result=p.read_profile(session)
    assert not result['exists'] and result['revision']==0
    assert 'Lavoro dipendente' in result['content_markdown']
    assert session.commits==0 and len(session.queries)==1

def test_first_save_creates_authoritative_document():
    session=Session()
    result=p.save_profile(p.ProfileUpdate(content_markdown='Desidero rimanere ai margini nel lavoro dipendente.',revision=0),session)
    assert result['revision']==1 and result['exists']
    assert session.commits==1
    assert session.logged[1:4]==('personal_profile','profile','create')
    assert not any('strategic_memories' in q or 'sb2_projects' in q for q in session.queries)

def test_refinement_updates_revision_and_logs_previous_document():
    before={'id':'profile','content_markdown':'Prima priorità','revision':2,'updated_at':'yesterday'}
    session=Session(before)
    result=p.save_profile(p.ProfileUpdate(content_markdown='Priorità affinata: proteggere il tempo di scrittura.',revision=2),session)
    assert result['revision']==3
    assert session.logged[4]==before
    assert session.logged[5]['content_markdown']==result['content_markdown']

def test_concurrent_change_does_not_overwrite_saved_profile():
    session=Session({'revision':4})
    with pytest.raises(HTTPException) as exc:
        p.save_profile(p.ProfileUpdate(content_markdown='Modifica da una vecchia scheda',revision=3),session)
    assert exc.value.status_code==409 and session.commits==0
    assert not any(q.startswith(('INSERT','UPDATE')) for q in session.queries)

def test_blank_profile_is_rejected():
    with pytest.raises(ValidationError):p.ProfileUpdate(content_markdown='   ',revision=0)
