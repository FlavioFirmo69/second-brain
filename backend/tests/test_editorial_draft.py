import asyncio
import json
from uuid import uuid4
import pytest
from app import work

@pytest.mark.parametrize('prompt',[
    'Scrivi il testo per Substack: Kanban',
    'Prepara una bozza articolo per Rubicone',
    'Vorrei il testo completo della newsletter'])
def test_article_request_is_recognized(prompt):assert work.is_article_request(prompt)

def test_calendar_question_is_not_article_request():
    assert not work.is_article_request('Quando devo pubblicare su Substack?')

def test_mailing_request_is_recognized():
    assert work.is_article_request('Scrivi il testo per la mailing list: Arona')

def test_mailing_draft_uses_subject_and_email_format(monkeypatch):
    data={'project':{'title':'Il subbuteo si racconta'},'author':{'code':'FLAVIO','voice_markdown':'Voce narrativa e autentica'},
          'requested_task':{'title':'Mailing: Arona — incontrare la storia e chi l’ha vissuta'}}
    async def complete(messages,**kwargs):
        assert 'title contiene l’oggetto' in messages[0]['content']
        assert 'Il subbuteo si racconta' in messages[0]['content']
        assert 'Voce narrativa e autentica' in messages[0]['content']
        return json.dumps({'title':'Arona, una storia da incontrare','subtitle':'Le persone dietro il racconto',
                           'content_markdown':'Una bozza narrativa per la mailing list, senza inventare date o dettagli dell’incontro. '*4})
    monkeypatch.setattr(work,'complete',complete)
    result=asyncio.run(work.draft_book_article(None,{},'Scrivi il testo per Mailing: Arona',[],data=data))
    assert result['kind']=='article' and result['data']['content_format']=='email'
    assert result['data']['author_code']=='FLAVIO'

def test_rubicone_scoped_chat_generates_article_with_cesare_profile_and_copy_metadata(monkeypatch):
    bid=uuid4()
    monkeypatch.setattr(work,'context',lambda *a:{'id':bid,'title':'Rubicone','author_profile_id':'cesare'})
    monkeypatch.setattr(work,'overview',lambda *a:(_ for _ in ()).throw(AssertionError('Not a calendar request')))
    data={'book':{'title':'Rubicone'},'author':{'code':'CESARE','voice_markdown':'Diretto, concreto, senza retorica'},
          'strategies':[{'content_markdown':'Lean: rendere visibili le contraddizioni organizzative'}],
          'tasks':[{'title':'Substack: Kanban — rendere visibile il lavoro che tutti fingono di controllare'}]}
    monkeypatch.setattr(work,'editorial_context',lambda *a:data)
    async def complete(messages,**kwargs):
        assert 'Diretto, concreto, senza retorica' in messages[0]['content']
        assert 'Lean: rendere visibili' in messages[0]['content']
        return json.dumps({'title':'Kanban','subtitle':'Rendere visibile il lavoro','content_markdown':'Testo completo nella voce di Cesare. '*20})
    monkeypatch.setattr(work,'complete',complete)
    result=asyncio.run(work.scoped_answer(None,{'book_id':bid,'case_id':None},'Scrivi il testo completo per Substack',[]))
    assert result['kind']=='article'
    assert result['data']['author_code']=='CESARE'
    assert 'content_markdown' in result['data'] and 'actions' not in result['data']
