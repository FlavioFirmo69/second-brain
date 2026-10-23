"""Verify the actual request contains cross-domain evidence, even for unnamed books.

These tests verify orchestration and safeguards; model quality needs a synthetic live check.
"""
import asyncio
from contextlib import nullcontext
from uuid import uuid4
import pytest
from app import strategic as s
from app.strategic_context import compact_context


@pytest.mark.parametrize('mode', ['advice', 'diary'])
def test_arona_encounter_reaches_other_author_strategy_without_book_mention(monkeypatch, mode):
    diary='Ad Arona incontrerò Maurizio, direttore vendite di una PMI.'
    context={'date':'2026-10-23','unavailable':[], 'sources':{
        'personal_profiles':[{'content_markdown':'Proteggere il tempo personale e sviluppare la scrittura indipendente.'}],
        'author_profiles':[{'id':'cesare','code':'CESARE','positioning':'Organizzazione del lavoro'}],
        'books':[{'id':'rubicone','author_profile_id':'cesare','title':'Rubicone',
                  'target_reader':'Responsabili commerciali di PMI','positioning':'Organizzazione del lavoro commerciale'}],
        'strategies':[{'id':'strategy','status':'active','author_profile_id':'cesare','book_id':'rubicone',
                       'content_markdown':'Raggiungere responsabili commerciali di PMI tramite letture e testimonianze autentiche.'}],
        'events':[{'id':'arona','title':'Evento Arona','event_date':'2026-11-01'}]}}
    calls=[]
    class Repo:
        def __init__(self,session):pass
        def create_conversation(self,title):return {'id':uuid4()}
        def add_conversation_message(self,*args):pass
    class Session:
        def begin_nested(self):return nullcontext()
        def execute(self,*args):raise AssertionError('No task/project/memory mutation allowed')
    monkeypatch.setattr(s,'Repository',Repo)
    monkeypatch.setattr(s,'official_context',lambda session:context)
    monkeypatch.setattr(s,'memories',lambda session:[])
    monkeypatch.setattr(s,'diary_context',lambda session:{'entries':[{'content_markdown':diary}]})
    async def extract(*args):return {'saved':[],'unavailable':False}
    monkeypatch.setattr(s,'extract_memories',extract)
    async def complete(messages,**kwargs):
        calls.append(messages)
        system=messages[0]['content']
        data=messages[-2]['content']
        assert 'Responsabili commerciali di PMI' in data
        assert 'strategy' in data and 'Organizzazione del lavoro commerciale' in data
        assert diary in (data+messages[-1]['content'])
        assert 'fatto riferito' in system and 'SE' in system
        assert 'consenso' in system and 'non creare attività' in system
        return 'Ipotesi: sondare interesse in conversazione, senza impegni.'
    monkeypatch.setattr(s,'complete',complete)
    prompt=diary if mode=='diary' else 'Dammi un quadro complessivo.'
    result=asyncio.run(s.advice(s.Question(text=prompt,mode=mode),Session()))
    assert not result['error'] and len(calls)==1


def test_all_book_audiences_survive_for_semantic_cross_domain_matching():
    book={'id':'b','title':'Romanzo','target_reader':'Direttori vendite PMI',
          'themes':'Autonomia','positioning':'Lavoro e organizzazione','differentiators':'Esperienza diretta'}
    projected=compact_context({'sources':{'books':[book]}},relevant_text='Oggi incontro un conoscente')
    assert projected['sources']['books']==[book]
