from datetime import date
from uuid import uuid4
import pytest
from pydantic import ValidationError
from app.schemas import ReleaseTargetUpdate
from app.repository import Repository
from app.strategic_context import compact_context


def test_target_accepts_clear_and_validates_date():
    assert ReleaseTargetUpdate().planned_release_date is None
    assert ReleaseTargetUpdate(planned_release_date='2027-03-30').planned_release_date == date(2027,3,30)
    with pytest.raises(ValidationError):
        ReleaseTargetUpdate(planned_release_date='2027-02-30')


@pytest.mark.parametrize('found',[True,False])
def test_target_changes_only_owned_book_planning(found):
    identity=uuid4()
    class Session:
        queries=[]
        commits=0
        def execute(self,query,args):
            self.queries.append(str(query))
            if len(self.queries)==1:assert args['uid']=='owner'
            return self
        def mappings(self):return self
        def one_or_none(self):return {'id':identity} if found else None
        def one(self):return {'id':identity,'planned_release_date':date(2027,3,30),'release_plan_note':None}
        def commit(self):self.commits+=1
    session=Session()
    repo=Repository(session)
    repo.user_id=lambda:'owner'
    repo.log=lambda *args:None
    payload=ReleaseTargetUpdate(planned_release_date='2027-03-30').model_dump()
    if not found:
        with pytest.raises(KeyError):repo.update_release_target(identity,payload)
        assert session.commits==0 and len(session.queries)==1
        return
    assert repo.update_release_target(identity,payload)['planned_release_date']==date(2027,3,30)
    assert session.commits==1
    assert 'a.user_id=:uid' in session.queries[0]
    update=session.queries[1].split('RETURNING')[0]
    assert 'WHERE id=:id' in update
    assert 'status=' not in update and 'publication_date=' not in update
    assert 'sb2_tasks' not in update


def test_adviser_context_preserves_separate_target_date():
    book={'id':'b','planned_release_date':'2027-03-30','release_plan_note':'Indicativa'}
    result=compact_context({'sources':{'books':[book]}})
    assert result['sources']['books'][0]['planned_release_date']=='2027-03-30'
    assert result['sources']['books'][0]['release_plan_note']=='Indicativa'
