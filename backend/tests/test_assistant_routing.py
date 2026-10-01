import asyncio
from datetime import date
from app import assistant

class FakeRepo:
    def __init__(self, session): pass
    def today(self): return date(2026,10,1)
    def profiles(self): return []
    def strategies(self): return []
    def books(self): return []
    def strategy_monitoring(self): return []
    def projects(self): return []
    def cases(self): return []
    def search_calendar(self, **kwargs): return {'tasks':[], 'events':[]}


def test_post_with_when_is_conversation(monkeypatch):
    monkeypatch.setattr(assistant,'Repository',FakeRepo)
    async def complete(*args,**kwargs): return '{"action":"respond","text":"Parliamone"}'
    monkeypatch.setattr(assistant,'complete',complete)
    prompt='Vorrei un consiglio per Cesare.\nPost: quando ho un problema il progettista no.\nCome potrei rispondere? Voglio soltanto discuterne con te.'
    result=asyncio.run(assistant.answer(None,prompt))
    assert result['kind']=='text' and result['mode']=='llm'


def test_standalone_calendar_question(monkeypatch):
    monkeypatch.setattr(assistant,'Repository',FakeRepo)
    result=asyncio.run(assistant.answer(None,'Quando devo andare dal dentista?'))
    assert result['kind']=='calendar_query'
