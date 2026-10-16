"""Inbox recovery and note context, using the existing inbox/chat stores."""
import json
from uuid import UUID
from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from .database import get_session
from .repository import Repository
from .schemas import InboxUpdate
from .assistant import answer

router=APIRouter(prefix='/api/inbox',tags=['Inbox'])

def owned(session,identity):
    row=session.execute(text('SELECT * FROM sb2_inbox WHERE id=:id AND user_id=:uid'),
                        {'id':identity,'uid':Repository(session).user_id()}).mappings().one_or_none()
    if row is None:raise HTTPException(404,'Elemento inbox non trovato')
    return dict(row)

def details(row):return json.loads(row.get('interpretation_json') or '{}')

def update_details(session,identity,value):
    session.execute(text('UPDATE sb2_inbox SET interpretation_json=:details WHERE id=:id AND user_id=:uid'),
        {'id':identity,'uid':Repository(session).user_id(),'details':json.dumps(value,ensure_ascii=False,default=str)})
    session.commit()

@router.patch('/{identity}')
def edit(identity:UUID,payload:InboxUpdate,session:Session=Depends(get_session)):
    row=owned(session,identity)
    if row['status']!='new':raise HTTPException(409,'L’elemento non è modificabile mentre è elaborato o archiviato')
    if not payload.text.strip():raise HTTPException(422,'Inserisci un testo')
    if payload.project_id and payload.case_id:raise HTTPException(422,'Scegli un progetto oppure una pratica')
    uid=Repository(session).user_id()
    for kind,ref in [('projects',payload.project_id),('cases',payload.case_id)]:
        if ref and session.execute(text(f'SELECT id FROM sb2_{kind} WHERE id=:id AND user_id=:uid'),{'id':ref,'uid':uid}).scalar_one_or_none() is None:
            raise HTTPException(404,'Contesto non trovato')
    data=details(row)
    if (payload.text.strip()!=row['text'] or str(payload.project_id or '')!=str(data.get('project_id') or '')
            or str(payload.case_id or '')!=str(data.get('case_id') or '')):
        data.pop('conversation_id',None)
    data.update(project_id=str(payload.project_id) if payload.project_id else None,case_id=str(payload.case_id) if payload.case_id else None)
    session.execute(text("UPDATE sb2_inbox SET text=:text,source=:source,interpretation_json=:details WHERE id=:id AND user_id=:uid"),
        {'id':identity,'uid':uid,'text':payload.text.strip(),'source':'llm_failed' if payload.category=='retry' else 'desktop','details':json.dumps(data,ensure_ascii=False)})
    session.commit()
    return {'id':identity}

@router.post('/{identity}/archive')
def archive(identity:UUID,session:Session=Depends(get_session)):
    row=owned(session,identity)
    if row['status']=='interpreted':raise HTTPException(409,'Attendi il termine dell’elaborazione')
    session.execute(text("UPDATE sb2_inbox SET status='confirmed',processed_at=now() WHERE id=:id AND user_id=:uid"),{'id':identity,'uid':Repository(session).user_id()})
    session.commit()
    return {'id':identity}

@router.post('/{identity}/open')
def open_note(identity:UUID,session:Session=Depends(get_session)):
    row=owned(session,identity);repo=Repository(session);data=details(row)
    if data.get('conversation_id'):
        found=session.execute(text('SELECT id FROM sb2_conversations WHERE id=:id AND user_id=:uid'),{'id':data['conversation_id'],'uid':repo.user_id()}).scalar_one_or_none()
        if found:return {'conversation_id':found}
    cid=repo.create_conversation('Appunto da chiarire')['id']
    note=row['text']
    for kind,key in [('projects','project_id'),('cases','case_id')]:
        if data.get(key):
            title=session.execute(text(f'SELECT title FROM sb2_{kind} WHERE id=:id AND user_id=:uid'),{'id':data[key],'uid':repo.user_id()}).scalar_one_or_none()
            if title:note+='\nContesto collegato: '+title
    repo.add_conversation_message(cid,'user',note if data.get('result') else 'Aiutami a dare contesto a questo appunto, senza creare impegni automaticamente:\n'+note)
    if data.get('result'):
        result=data['result'];payload=result.get('data') or {}
        content=payload.get('content_markdown') if result.get('kind')=='article' else result.get('message') or payload.get('text') or 'Richiesta elaborata.'
        repo.add_conversation_message(cid,'assistant',content,result.get('kind','text'),payload if result.get('kind')=='article' else {'result':result})
    else:
        repo.add_conversation_message(cid,'assistant','Appunto caricato. Scrivi qui cosa vuoi chiarire o come vuoi usarlo: il collegamento a un progetto non crea automaticamente un’attività.')
    data['conversation_id']=str(cid)
    update_details(session,identity,data)
    return {'conversation_id':cid}

@router.post('/{identity}/retry')
async def retry_inbox(identity:UUID,session:Session=Depends(get_session)):
    repo=Repository(session);row=owned(session,identity)
    if row['status']!='new':raise HTTPException(409,'Richiesta già elaborata o in elaborazione')
    if row['source'] not in ('llm_failed','assistant'):raise HTTPException(409,'Questo è un appunto: aprilo nell’assistente per contestualizzarlo')
    claimed=session.execute(text("UPDATE sb2_inbox SET status='interpreted',processed_at=now() WHERE id=:id AND user_id=:uid AND status='new' RETURNING id"),{'id':identity,'uid':repo.user_id()}).scalar_one_or_none()
    session.commit()
    if claimed is None:raise HTTPException(409,'La richiesta è già in elaborazione')
    data=details(row)
    prompt=row['text']
    # Context is stored as references only; retrieve the current official title each time.
    for kind,key in [('projects','project_id'),('cases','case_id')]:
        if data.get(key):
            title=session.execute(text(f'SELECT title FROM sb2_{kind} WHERE id=:id AND user_id=:uid'),{'id':data[key],'uid':repo.user_id()}).scalar_one_or_none()
            if title:prompt+='\nContesto collegato: '+title
    completed_result=None
    try:
        result=await answer(session,prompt,failure_sink=lambda error:repo.set_inbox_error(identity,error))
        if result.get('mode')=='queued':return {'resolved':False,'message':result.get('message','Richiesta non riuscita')}
        completed_result=result
        cid=repo.create_conversation('Risultato richiesta Inbox')['id']
        repo.add_conversation_message(cid,'user',prompt)
        payload=result.get('data') or {}
        content=payload.get('content_markdown') if result.get('kind')=='article' else result.get('message') or payload.get('text') or 'Richiesta elaborata.'
        repo.add_conversation_message(cid,'assistant',content,result.get('kind','text'),payload if result.get('kind')=='article' else {'result':result})
        data.update(conversation_id=str(cid),result=result)
        repo.complete_inbox(identity,data)
        return {'resolved':True,'conversation_id':cid,'message':'Richiesta elaborata. Il risultato è disponibile nella conversazione.'}
    except Exception:
        session.rollback()
        if completed_result is not None:
            repo.complete_inbox(identity,{**data,'result':completed_result,'last_error':'Risultato prodotto; aprilo dall’archivio senza ripetere le operazioni.'})
        else:
            repo.set_inbox_error(identity,'Elaborazione non completata. Richiesta conservata: verifica lo stato prima di riprovare.')
        raise
