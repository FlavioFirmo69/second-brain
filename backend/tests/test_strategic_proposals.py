import json
from uuid import uuid4
import pytest
from fastapi import HTTPException
from app import strategic_proposals as p


def context():
    return {'date':'2026-10-23','sources':{'strategies':[
        {'id':'cesare','status':'active'},{'id':'old','status':'archived'}]}}


def proposal():
    return {'id':str(uuid4()),'action':'Sondare con Maurizio l’interesse per una lettura di Cesare',
            'proposed_date':'2026-10-30','rationale':'Data indicativa per un primo contatto, da concordare.',
            'source_refs':['strategies:cesare'],'status':'proposed'}


def test_proposals_require_real_active_references_and_future_dates():
    valid=proposal()
    archived={**valid,'source_refs':['strategies:old']}
    invented={**valid,'source_refs':['strategies:invented']}
    expired={**valid,'proposed_date':'2026-01-01'}
    for rejected in (archived,invented,expired):
        answer,items=p.parse_advice(json.dumps({'answer':'Valutazione','proposals':[rejected]}),context())
        assert answer=='Valutazione' and items==[]
    answer,items=p.parse_advice(json.dumps({'answer':'Valutazione','proposals':[valid]}),context())
    assert items[0]['status']=='proposed' and items[0]['id']!=valid['id']
    assert items[0]['proposed_date']=='2026-10-30'


@pytest.mark.parametrize('raw',['Risposta precedente','null','[]','{"answer":"Risposta", "proposals":null}'])
def test_plain_or_unusable_proposals_never_create_actions(raw):
    answer,items=p.parse_advice(raw,context())
    assert isinstance(answer,str) and not items


class Session:
    def __init__(self,item=None,owned=True):
        self.proposal=item or proposal()
        self.metadata={'strategic_proposals':[self.proposal]}
        self.sql=[];self.params=[];self.commits=0;self.owned=owned
        self.entry_id=uuid4();self.cid=uuid4()
        self.current_strategy={'id':'cesare','title':'Lettori di Rubicone','status':'active','author_name':'Cesare','book_title':'Rubicone'}
    def execute(self,query,args):
        self.sql.append(str(query));self.params.append(args)
        if len(self.sql)==1:
            assert args['uid']=='owner' and 'c.user_id=:uid' in str(query) and 'FOR UPDATE OF m' in str(query)
        return self
    def mappings(self):return self
    def one_or_none(self):
        if 'FROM sb2_strategies' in self.sql[-1]:
            assert self.params[-1]['uid']=='owner' and 's.user_id=:uid' in self.sql[-1]
            return self.current_strategy
        return {'conversation_id':self.cid,'metadata_json':json.dumps(self.metadata)} if self.owned else None
    def scalar_one(self):return self.entry_id
    def commit(self):self.commits+=1


@pytest.fixture(autouse=True)
def repo(monkeypatch):
    class Repo:
        def __init__(self,session):pass
        def user_id(self):return 'owner'
        def today(self):return '2026-10-23'
    monkeypatch.setattr(p,'Repository',Repo)


def decide(session,**payload):
    return p.decide_proposal(uuid4(),session.proposal['id'],p.ProposalDecision(**payload),session)


def test_accept_records_intention_in_existing_diary_with_edited_date_and_no_operational_changes():
    session=Session()
    result=decide(session,decision='accepted',planned_date='2026-11-02')
    assert result['proposal']['planned_date']=='2026-11-02'
    assert result['proposal']['status']=='accepted' and session.commits==1
    content=next(args['content'] for args in session.params if 'content' in args)
    assert '02/11/2026' in content and 'non un’azione già eseguita' in content
    assert any("'strategic_diary'" in sql for sql in session.sql)
    assert not any(table in '\n'.join(session.sql) for table in ['sb2_tasks','sb2_events','sb2_strategic_memories'])
    stored=json.loads(next(args['metadata'] for sql,args in zip(session.sql,session.params) if 'UPDATE sb2_messages' in sql))['strategic_proposals'][0]
    assert stored['diary_entry_id']==str(session.entry_id)
    assert stored['strategy_ids']==['cesare']
    assert 'Strategia collegata: Lettori di Rubicone · Cesare · Rubicone' in content
    diary=json.loads(next(args['metadata'] for args in session.params if 'content' in args))
    assert diary['strategic_decision']['strategy_ids']==['cesare']


def test_reject_requires_nonblank_reason_before_any_write():
    session=Session()
    with pytest.raises(HTTPException) as exc:decide(session,decision='rejected',reason='   ')
    assert exc.value.status_code==422 and not session.sql and session.commits==0


def test_reject_preserves_reason_in_diary_for_future_advice():
    session=Session()
    result=decide(session,decision='rejected',reason='Preferisco parlarne ad Arona.')
    assert result['proposal']['reason']=='Preferisco parlarne ad Arona.'
    assert 'Preferisco parlarne ad Arona.' in session.params[1]['content']
    assert 'non implica una preferenza generale' in session.params[1]['content']
    assert session.commits==1


def test_repeated_acceptance_is_idempotent_and_opposite_decision_conflicts():
    item={**proposal(),'status':'accepted','diary_entry_id':str(uuid4())}
    session=Session(item)
    result=decide(session,decision='accepted')
    assert result['already_recorded'] and len(session.sql)==1 and session.commits==0
    session=Session(item)
    with pytest.raises(HTTPException) as exc:decide(session,decision='rejected',reason='Ho cambiato idea')
    assert exc.value.status_code==409 and len(session.sql)==1


def test_other_users_proposal_is_inaccessible():
    session=Session(owned=False)
    with pytest.raises(HTTPException) as exc:decide(session,decision='accepted')
    assert exc.value.status_code==404 and session.commits==0


def test_past_accepted_date_is_rejected_without_diary_insert():
    session=Session()
    with pytest.raises(HTTPException) as exc:decide(session,decision='accepted',planned_date='2026-01-01')
    assert exc.value.status_code==422 and len(session.sql)==1 and session.commits==0


@pytest.mark.parametrize('strategy',[None,{'status':'archived'}])
def test_accept_rechecks_strategy_access_and_state_before_recording(strategy):
    session=Session()
    session.current_strategy=strategy
    with pytest.raises(HTTPException) as exc:decide(session,decision='accepted')
    assert exc.value.status_code==409 and session.commits==0
    assert not any('INSERT' in sql for sql in session.sql)


def test_selected_strategy_labels_come_from_official_records_and_not_first_author():
    sources={'author_profiles':[{'id':'flavio','display_name':'Flavio'},{'id':'cesare','display_name':'Cesare'}],
             'books':[{'id':'rubicone','title':'Rubicone','author_profile_id':'cesare'}],
             'strategies':[{'id':'f','title':'Altra strategia','author_profile_id':'flavio','status':'active'},
                           {'id':'c','title':'Lettori PMI','book_id':'rubicone','status':'active'}]}
    raw=json.dumps({'answer':'Collegamento a Cesare','proposals':[{**proposal(),'source_refs':['strategies:c']}]})
    _,items=p.parse_advice(raw,{'date':'2026-10-23','sources':sources})
    assert items[0]['strategy_ids']==['c']
    assert items[0]['strategy_links']==[{'id':'c','title':'Lettori PMI','author_name':'Cesare','book_title':'Rubicone'}]


def test_author_profile_alone_does_not_substitute_for_editorial_strategy():
    raw=json.dumps({'answer':'Serve precisare la strategia','proposals':[{**proposal(),'source_refs':['author_profiles:c']}]})
    _,items=p.parse_advice(raw,{'date':'2026-10-23','sources':{'author_profiles':[{'id':'c','display_name':'Cesare'}]}})
    assert not items
