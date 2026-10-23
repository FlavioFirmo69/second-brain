import asyncio
from types import SimpleNamespace
import httpx
import pytest
from app import llm

@pytest.fixture
def configured(monkeypatch):
    settings=SimpleNamespace(llm_enabled=True,llm_api_key='test-private-key',llm_model='test-model',llm_base_url='https://provider.invalid/v1')
    monkeypatch.setattr(llm,'get_settings',lambda:settings)
    return settings

def client(monkeypatch,status=200,payload=None,error=None,headers=None):
    requests=[]
    class Client:
        def __init__(self,**kwargs):pass
        async def __aenter__(self):return self
        async def __aexit__(self,*args):pass
        async def post(self,url,**kwargs):
            requests.append(kwargs)
            if error:raise error
            return httpx.Response(status,json=payload,headers=headers,request=httpx.Request('POST',url))
    monkeypatch.setattr(llm.httpx,'AsyncClient',Client)
    async def sleep(*args):pass
    monkeypatch.setattr(llm.asyncio,'sleep',sleep)
    return requests

def test_valid_text_response(configured,monkeypatch):
    client(monkeypatch,payload={'choices':[{'message':{'content':'Consiglio di prova'}}]})
    assert asyncio.run(llm.complete([{'role':'user','content':'Domanda sintetica'}]))=='Consiglio di prova'

@pytest.mark.parametrize('status,code',[(400,'invalid_request'),(401,'authentication'),(403,'authentication'),(404,'model_or_endpoint'),(413,'invalid_request'),(429,'rate_limit'),(503,'provider_error')])
def test_failure_reason_is_specific_without_exposing_provider_body(configured,monkeypatch,status,code):
    requests=client(monkeypatch,status=status,payload={'error':{'message':'test-private-key confidential provider body'}})
    with pytest.raises(llm.LlmUnavailable) as exc:
        asyncio.run(llm.complete([{'role':'user','content':'Synthetic'}]))
    assert exc.value.code==code and exc.value.status==status
    assert 'test-private-key' not in str(exc.value) and 'confidential' not in str(exc.value)
    assert len(requests)==(3 if status in (429,503) else 1)

@pytest.mark.parametrize('content',[None,'',[], '   '])
def test_empty_response_is_not_reported_as_success(configured,monkeypatch,content):
    client(monkeypatch,payload={'choices':[{'message':{'content':content}}]})
    with pytest.raises(llm.LlmUnavailable) as exc:asyncio.run(llm.complete([]))
    assert exc.value.code=='empty_response'

def test_missing_choices_is_a_safe_format_error(configured,monkeypatch):
    client(monkeypatch,payload={'choices':[]})
    with pytest.raises(llm.LlmUnavailable) as exc:asyncio.run(llm.complete([]))
    assert exc.value.code=='invalid_response'

def test_timeout_is_distinguishable_from_unconfigured_model(configured,monkeypatch):
    requests=client(monkeypatch,error=httpx.ReadTimeout('private request details'))
    with pytest.raises(llm.LlmUnavailable) as exc:asyncio.run(llm.complete([]))
    assert exc.value.code=='timeout' and 'private request details' not in str(exc.value)
    assert len(requests)==3


@pytest.mark.parametrize('first',[httpx.ReadTimeout('private'),httpx.ConnectError('private'),408,503])
def test_transient_failure_recovers_without_changing_the_request(configured,monkeypatch,first):
    requests=[]
    class Client:
        def __init__(self,**kwargs):pass
        async def __aenter__(self):return self
        async def __aexit__(self,*args):pass
        async def post(self,url,**kwargs):
            requests.append(kwargs)
            if len(requests)==1:
                if isinstance(first,Exception):raise first
                return httpx.Response(first,request=httpx.Request('POST',url))
            return httpx.Response(200,json={'choices':[{'message':{'content':'OK'}}]})
    monkeypatch.setattr(llm.httpx,'AsyncClient',Client)
    async def sleep(*args):pass
    monkeypatch.setattr(llm.asyncio,'sleep',sleep)
    assert asyncio.run(llm.complete([{'role':'user','content':'Test'}]))=='OK'
    assert len(requests)==2 and requests[0]==requests[1]

def test_not_configured_does_not_claim_inbox_write(configured):
    configured.llm_enabled=False
    with pytest.raises(llm.LlmUnavailable) as exc:asyncio.run(llm.complete([]))
    assert exc.value.code=='not_configured' and 'inbox' not in str(exc.value)

def test_multiple_system_instructions_are_preserved_in_one_message(configured,monkeypatch):
    requests=client(monkeypatch,payload={'choices':[{'message':{'content':'OK'}}]})
    asyncio.run(llm.complete([{'role':'system','content':'Prima regola'},
        {'role':'system','content':'Seconda regola'}, {'role':'user','content':'Testo sintetico'}]))
    assert requests[0]['json']['messages']==[
        {'role':'system','content':'Prima regola\n\nSeconda regola'}, {'role':'user','content':'Testo sintetico'}]
