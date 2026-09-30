"""Versioned plans: no operational writes before explicit approval."""
import json
from datetime import date
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from .database import get_session
from .repository import Repository, rows
from .llm import complete, LlmUnavailable
from .schemas import TaskCreate, EventCreate
from .planning_models import CaseInput, PlanInput, TurnInput, RevisionInput, DraftInput, Draft, CoverageInput

router = APIRouter(prefix='/api/planning', tags=['Piani e pratiche'])


def owned_case(session, uid, case_id):
    item = session.execute(text('SELECT * FROM sb2_cases WHERE id=:id AND user_id=:uid'), {'id': case_id, 'uid': uid}).mappings().one_or_none()
    if not item:
        raise HTTPException(404, 'Pratica non trovata')
    return dict(item)


def plan(session, uid, plan_id, lock=False):
    item = session.execute(text('SELECT * FROM sb2_plans WHERE id=:id AND user_id=:uid' + (' FOR UPDATE' if lock else '')), {'id': plan_id, 'uid': uid}).mappings().one_or_none()
    if not item:
        raise HTTPException(404, 'Piano non trovato')
    return dict(item)


def ensure_editable(item, revision):
    if item['status'] not in ('interview', 'draft'):
        raise HTTPException(409, 'Piano non modificabile: pulire o creare una nuova bozza')
    if item['revision'] != revision:
        raise HTTPException(409, 'Piano aggiornato da un’altra richiesta: ricaricare')


def source(session, uid, item):
    if item['case_id']:
        return owned_case(session, uid, item['case_id'])
    data = session.execute(text('''SELECT b.*,a.code AS author_code,a.display_name AS author_name,
        a.voice_markdown,a.positioning AS author_positioning FROM sb2_books b
        JOIN sb2_author_profiles a ON a.id=b.author_profile_id WHERE b.id=:id AND a.user_id=:uid'''), {'id': item['book_id'], 'uid': uid}).mappings().one_or_none()
    if not data:
        raise HTTPException(404, 'Libro non trovato')
    return dict(data)


def log(session, uid, entity_id, action, data):
    Repository(session).log(uid, 'plan', entity_id, action, None, data)


@router.post('/cases')
def create_case(payload: CaseInput, session: Session = Depends(get_session)):
    uid = Repository(session).user_id()
    if session.execute(text('SELECT 1 FROM sb2_cases WHERE user_id=:uid AND UPPER(code)=:code'), {'uid': uid, 'code': payload.code.upper()}).scalar():
        raise HTTPException(409, 'Codice pratica già presente')
    item = session.execute(text('''INSERT INTO sb2_cases(user_id,code,title,status,context_markdown)
        VALUES(:uid,:code,:title,'active',:context_markdown) RETURNING *'''), {'uid': uid, **payload.model_dump(), 'code': payload.code.upper()}).mappings().one()
    session.commit()
    return dict(item)


@router.get('/cases/{case_id}')
def case_detail(case_id: UUID, session: Session = Depends(get_session)):
    uid = Repository(session).user_id()
    item = owned_case(session, uid, case_id)
    for kind, table in [('tasks', 'sb2_tasks'), ('events', 'sb2_events')]:
        item[kind] = rows(session.execute(text(f'SELECT * FROM {table} WHERE case_id=:id AND user_id=:uid ORDER BY created_at DESC'), {'id': case_id, 'uid': uid}))
    return item


@router.put('/cases/{case_id}')
def update_case(case_id: UUID, payload: CaseInput, session: Session = Depends(get_session)):
    uid = Repository(session).user_id()
    owned_case(session, uid, case_id)
    if session.execute(text('SELECT 1 FROM sb2_cases WHERE user_id=:uid AND UPPER(code)=:code AND id<>:id'), {'uid': uid, 'code': payload.code.upper(), 'id': case_id}).scalar():
        raise HTTPException(409, 'Codice pratica già presente')
    session.execute(text('UPDATE sb2_cases SET code=:code,title=:title,context_markdown=:context_markdown,updated_at=now() WHERE id=:id AND user_id=:uid'), {'id': case_id, 'uid': uid, **payload.model_dump(), 'code': payload.code.upper()})
    session.commit()
    return case_detail(case_id, session)


@router.post('/cases/{case_id}/tasks')
def manual_task(case_id: UUID, payload: TaskCreate, session: Session = Depends(get_session)):
    uid = Repository(session).user_id()
    owned_case(session, uid, case_id)
    if payload.due_time and not payload.due_date:
        raise HTTPException(422, 'Un orario richiede una data')
    data = payload.model_dump()
    data.update(case_id=case_id, project_id=None, book_id=None, author_profile_id=None)
    return Repository(session).create_task(data)


@router.post('/cases/{case_id}/events')
def manual_event(case_id: UUID, payload: EventCreate, session: Session = Depends(get_session)):
    uid = Repository(session).user_id()
    owned_case(session, uid, case_id)
    if payload.end_time and (not payload.start_time or payload.end_time <= payload.start_time):
        raise HTTPException(422, 'Intervallo orario non valido')
    data = payload.model_dump()
    data.update(case_id=case_id, project_id=None, book_id=None, author_profile_id=None)
    return Repository(session).create_event(data)


@router.get('/plans')
def list_plans(session: Session = Depends(get_session)):
    uid = Repository(session).user_id()
    return rows(session.execute(text('''SELECT p.*,COALESCE(b.title,c.title) AS context_title,
        a.display_name AS author_name FROM sb2_plans p LEFT JOIN sb2_books b ON b.id=p.book_id
        LEFT JOIN sb2_author_profiles a ON a.id=b.author_profile_id LEFT JOIN sb2_cases c ON c.id=p.case_id
        WHERE p.user_id=:uid ORDER BY p.created_at DESC'''), {'uid': uid}))


@router.post('/plans')
def create_plan(payload: PlanInput, session: Session = Depends(get_session)):
    uid = Repository(session).user_id()
    source(session, uid, payload.model_dump())
    item = session.execute(text('''INSERT INTO sb2_plans(user_id,case_id,book_id,brief)
        VALUES(:uid,:case_id,:book_id,:brief) RETURNING *'''), {'uid': uid, **payload.model_dump()}).mappings().one()
    session.commit()
    return dict(item)


@router.get('/plans/{plan_id}')
def detail(plan_id: UUID, session: Session = Depends(get_session)):
    uid = Repository(session).user_id()
    item = plan(session, uid, plan_id)
    for kind, table in [('tasks', 'sb2_tasks'), ('events', 'sb2_events')]:
        item[kind] = rows(session.execute(text(f'''WITH RECURSIVE tree AS (
            SELECT id FROM sb2_plans WHERE id=:id AND user_id=:uid UNION ALL
            SELECT p.id FROM sb2_plans p JOIN tree t ON p.parent_id=t.id WHERE p.user_id=:uid)
            SELECT * FROM {table} WHERE plan_id IN (SELECT id FROM tree) AND user_id=:uid ORDER BY created_at DESC'''), {'id': plan_id, 'uid': uid}))
    return item


async def model_json(messages):
    try:
        raw = await complete(messages, response_format={'type': 'json_object'})
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError('Risposta non strutturata')
        return value
    except LlmUnavailable as exc:
        raise HTTPException(503, 'LLM non disponibile: nessuna attività creata. Il piano è conservato.') from exc
    except (ValueError, TypeError) as exc:
        raise HTTPException(422, 'Risposta del modello non valida: nessuna attività creata') from exc


@router.post('/plans/{plan_id}/interview')
async def interview(plan_id: UUID, payload: TurnInput, session: Session = Depends(get_session)):
    uid = Repository(session).user_id()
    item = plan(session, uid, plan_id)
    ensure_editable(item, payload.revision)
    context = source(session, uid, item)
    history = item['dialogue'] + [{'role': 'user', 'content': payload.text}]
    session.commit()  # Never hold a database lock while calling a model.
    result = await model_json([
        {'role': 'system', 'content': 'Conduci un breve colloquio per un piano personale o una strategia di marketing editoriale. Usa solo il contesto selezionato. Non ripetere domande già risolte. Fai massimo 3 domande mirate per turno, spiega perché. Se sufficienti, riepiloga obiettivo, vincoli e ipotesi e invita a generare la bozza. Non creare attività. Non trattare ipotesi legali, fiscali, costi o date pensionistiche come fatti verificati. Non hai accesso web: indica quali fonti/documenti servono. Restituisci JSON {"text":"...","ready":true/false}.'},
        {'role': 'user', 'content': json.dumps({'today': str(Repository(session).today()), 'context': context, 'brief': item['brief'], 'dialogue': history}, default=str, ensure_ascii=False)}])
    if not isinstance(result.get('text'), str) or not result['text'].strip():
        raise HTTPException(422, 'Risposta colloquio incompleta')
    locked = plan(session, uid, plan_id, True)
    ensure_editable(locked, payload.revision)
    history.append({'role': 'assistant', 'content': result['text']})
    session.execute(text("UPDATE sb2_plans SET dialogue=CAST(:dialogue AS jsonb),status='interview',draft=NULL,revision=revision+1,updated_at=now() WHERE id=:id"), {'id': plan_id, 'dialogue': json.dumps(history)})
    session.commit()
    return detail(plan_id, session)


@router.post('/plans/{plan_id}/generate')
async def generate(plan_id: UUID, payload: RevisionInput, session: Session = Depends(get_session)):
    uid = Repository(session).user_id()
    item = plan(session, uid, plan_id)
    ensure_editable(item, payload.revision)
    if not any(turn['role'] == 'assistant' for turn in item['dialogue']):
        raise HTTPException(409, 'Avviare prima il colloquio')
    context = source(session, uid, item)
    session.commit()
    result = await model_json([
        {'role': 'system', 'content': 'Genera una BOZZA, mai attività operative. Per un libro sei specializzato in marketing editoriale: conserva autore e identità selezionati, target concordato e quarter richiesto; non inventare vendite o garanzie di risultato. Motiva sequenza, date, risultati attesi e soglia di scostamento (default 30%). milestone = copie cumulative attese a fine settimana, ultima a end_date uguale al target. Per pratica target_copies=null e milestones=[]. Distingui fatti forniti e ipotesi in assumptions; trasforma in verifiche i punti non documentati. Non hai accesso web. depends_on usa indici delle azioni precedenti a partire da zero e descrive prerequisiti; non inventare date per azioni ancora incerte. Tutte le date pianificate devono essere nel periodo. Restituisci un JSON conforme allo schema seguente: ' + json.dumps(Draft.model_json_schema())},
        {'role': 'user', 'content': json.dumps({'today': str(Repository(session).today()), 'context': context, 'brief': item['brief'], 'dialogue': item['dialogue']}, default=str, ensure_ascii=False)}])
    try:
        draft = Draft.model_validate(result)
    except ValueError as exc:
        raise HTTPException(422, 'Bozza non coerente: ' + str(exc)) from exc
    if item['book_id'] and not item['parent_id'] and not draft.target_copies:
        raise HTTPException(422, 'Una strategia editoriale richiede un target e aspettative cumulative')
    locked = plan(session, uid, plan_id, True)
    ensure_editable(locked, payload.revision)
    if json.dumps(source(session, uid, locked), default=str, sort_keys=True) != json.dumps(context, default=str, sort_keys=True):
        raise HTTPException(409, 'Scheda modificata durante la generazione: rigenerare')
    session.execute(text("UPDATE sb2_plans SET draft=CAST(:draft AS jsonb),source_snapshot=CAST(:snapshot AS jsonb),status='draft',revision=revision+1,updated_at=now() WHERE id=:id"), {'id': plan_id, 'draft': draft.model_dump_json(), 'snapshot': json.dumps(context, default=str)})
    session.commit()
    return detail(plan_id, session)


@router.put('/plans/{plan_id}/draft')
def save_draft(plan_id: UUID, payload: DraftInput, session: Session = Depends(get_session)):
    uid = Repository(session).user_id()
    item = plan(session, uid, plan_id, True)
    ensure_editable(item, payload.revision)
    if item['book_id'] and not item['parent_id'] and not payload.draft.target_copies:
        raise HTTPException(422, 'Target editoriale mancante')
    context = source(session, uid, item)
    if item.get('source_snapshot') and json.loads(json.dumps(context, default=str)) != item['source_snapshot']:
        raise HTTPException(409, 'Scheda modificata: rigenerare la bozza prima di salvarla')
    session.execute(text("UPDATE sb2_plans SET draft=CAST(:draft AS jsonb),source_snapshot=CAST(:snapshot AS jsonb),status='draft',revision=revision+1,updated_at=now() WHERE id=:id"), {'id': plan_id, 'draft': payload.draft.model_dump_json(), 'snapshot': json.dumps(context, default=str)})
    session.commit()
    return detail(plan_id, session)


@router.post('/plans/{plan_id}/approve')
def approve(plan_id: UUID, payload: RevisionInput, session: Session = Depends(get_session)):
    uid = Repository(session).user_id()
    # Serializes approvals for the same owner, including competing drafts.
    session.execute(text('SELECT id FROM sb2_users WHERE id=:uid FOR UPDATE'), {'uid': uid})
    item = plan(session, uid, plan_id, True)
    if item['status'] == 'active':
        return detail(plan_id, session)  # Idempotent repeated approval.
    ensure_editable(item, payload.revision)
    if item['status'] != 'draft' or not item['draft']:
        raise HTTPException(409, 'Generare e salvare prima una bozza')
    draft = Draft.model_validate(item['draft'])
    current_source = source(session, uid, item)
    if item.get('source_snapshot') and json.loads(json.dumps(current_source, default=str)) != item['source_snapshot']:
        raise HTTPException(409, 'La scheda è cambiata dopo la bozza: rigenerare prima di approvare')
    if item['parent_id']:
        parent = plan(session, uid, item['parent_id'], True)
        if parent['status'] != 'active':
            raise HTTPException(409, 'La strategia originale non è attiva')
        parent_draft = Draft.model_validate(parent['draft'])
        if draft.start_date < parent_draft.start_date or draft.end_date > parent_draft.end_date:
            raise HTTPException(422, 'La correzione deve restare nel periodo della strategia')
    else:
        conflict = session.execute(text('''SELECT id FROM sb2_plans WHERE user_id=:uid AND status='active' AND parent_id IS NULL
            AND (case_id=:case_id OR book_id=:book_id)'''), {'uid': uid, 'case_id': item['case_id'], 'book_id': item['book_id']}).scalar()
        if conflict:
            raise HTTPException(409, 'Esiste già un piano attivo: pulirlo prima di approvare il nuovo')
    context = source(session, uid, item)
    params = {'uid': uid, 'plan_id': plan_id, 'case_id': item['case_id'], 'book_id': item['book_id'], 'author_id': context.get('author_profile_id')}
    for index, action in enumerate(draft.actions):
        description = json.dumps({'reason': action.reason, 'expected_result': action.expected_result, 'depends_on': action.depends_on, 'action_index': index}, ensure_ascii=False)
        fields = {**params, 'title': action.title, 'description': description, 'day': action.date, 'start': action.start_time, 'end': action.end_time, 'location': action.location, 'priority': action.priority}
        if action.kind == 'task':
            session.execute(text('''INSERT INTO sb2_tasks(user_id,case_id,book_id,author_profile_id,plan_id,title,description,due_date,due_time,priority,source)
                VALUES(:uid,:case_id,:book_id,:author_id,:plan_id,:title,:description,:day,:start,:priority,'approved_plan')'''), fields)
        else:
            session.execute(text('''INSERT INTO sb2_events(user_id,case_id,book_id,author_profile_id,plan_id,title,event_date,start_time,end_time,location,event_type)
                VALUES(:uid,:case_id,:book_id,:author_id,:plan_id,:title,:day,:start,:end,:location,'plan')'''), fields)
    session.execute(text("UPDATE sb2_plans SET status='active',revision=revision+1,updated_at=now() WHERE id=:id"), {'id': plan_id})
    log(session, uid, plan_id, 'approve', {'actions': len(draft.actions), 'revision': item['revision']})
    session.commit()
    return detail(plan_id, session)


@router.post('/plans/{plan_id}/discard')
def discard(plan_id: UUID, payload: RevisionInput, session: Session = Depends(get_session)):
    uid = Repository(session).user_id()
    item = plan(session, uid, plan_id, True)
    ensure_editable(item, payload.revision)
    session.execute(text("UPDATE sb2_plans SET status='discarded',revision=revision+1,updated_at=now() WHERE id=:id"), {'id': plan_id})
    session.commit()
    return detail(plan_id, session)


@router.post('/plans/{plan_id}/clean')
def clean(plan_id: UUID, payload: RevisionInput, session: Session = Depends(get_session)):
    uid = Repository(session).user_id()
    session.execute(text('SELECT id FROM sb2_users WHERE id=:uid FOR UPDATE'), {'uid': uid})
    item = plan(session, uid, plan_id, True)
    if item['revision'] != payload.revision:
        raise HTTPException(409, 'Ricaricare il piano prima della pulizia')
    if item['status'] != 'active':
        raise HTTPException(409, 'La pulizia richiede un piano attivo')
    ids = list(session.execute(text('''WITH RECURSIVE tree AS (SELECT id FROM sb2_plans WHERE id=:id AND user_id=:uid
        UNION ALL SELECT p.id FROM sb2_plans p JOIN tree t ON p.parent_id=t.id WHERE p.user_id=:uid) SELECT id FROM tree'''), {'id': plan_id, 'uid': uid}).scalars())
    for child_id in ids:
        for table in ('sb2_tasks', 'sb2_events'):
            session.execute(text(f"UPDATE {table} SET status='cancelled',updated_at=now() WHERE user_id=:uid AND plan_id=:id AND status NOT IN ('completed','cancelled')"), {'id': child_id, 'uid': uid})
        session.execute(text("UPDATE sb2_plans SET status='cleaned',revision=revision+1,updated_at=now() WHERE id=:id AND user_id=:uid"), {'id': child_id, 'uid': uid})
    log(session, uid, plan_id, 'clean', {'plans': [str(i) for i in ids]})
    session.commit()
    return detail(plan_id, session)


def calculate_monitor(draft, through, actual):
    """Use only closed expectation checkpoints covered by confirmed data."""
    available = [point for point in draft.milestones if point.date <= through]
    expected = available[-1].cumulative_copies if available else 0
    deviation = (actual - expected) / expected * 100 if expected else None
    status = 'insufficient_history' if expected < draft.minimum_expected else ('below_threshold' if deviation <= -draft.threshold_percent else 'in_line')
    return {'expected': expected, 'actual': actual, 'deviation_percent': deviation, 'status': status}


@router.post('/plans/{plan_id}/coverage')
def coverage(plan_id: UUID, payload: CoverageInput, session: Session = Depends(get_session)):
    uid = Repository(session).user_id()
    item = plan(session, uid, plan_id, True)
    if not item['book_id'] or item['status'] != 'active' or item['parent_id']:
        raise HTTPException(409, 'Selezionare una strategia editoriale principale attiva')
    if payload.through > Repository(session).today():
        raise HTTPException(422, 'Non si possono confermare vendite future')
    session.execute(text('UPDATE sb2_plans SET sales_updated_through=:day,updated_at=now() WHERE id=:id'), {'id': plan_id, 'day': payload.through})
    session.commit()
    return monitor(plan_id, session)


@router.get('/plans/{plan_id}/monitor')
def monitor(plan_id: UUID, session: Session = Depends(get_session)):
    uid = Repository(session).user_id()
    item = plan(session, uid, plan_id)
    if not item['book_id'] or item['status'] != 'active' or item['parent_id']:
        raise HTTPException(409, 'Monitoraggio disponibile per strategie editoriali principali attive')
    draft = Draft.model_validate(item['draft'])
    today = Repository(session).today()
    completed_points = [p for p in draft.milestones if p.date <= min(today, draft.end_date)]
    if not completed_points:
        return {'status': 'insufficient_history', 'message': 'Nessun checkpoint di vendita ancora raggiunto'}
    checkpoint = completed_points[-1].date
    if not item['sales_updated_through'] or item['sales_updated_through'] < checkpoint:
        return {'status': 'data_missing', 'checkpoint': checkpoint, 'message': 'Confermare i dati di vendita fino al checkpoint, anche se non ci sono vendite'}
    actual = session.execute(text('SELECT COALESCE(SUM(quantity),0) FROM sb2_sales WHERE user_id=:uid AND book_id=:book_id AND sale_date BETWEEN :start AND :end'), {'uid': uid, 'book_id': item['book_id'], 'start': draft.start_date, 'end': checkpoint}).scalar_one()
    result = calculate_monitor(draft, checkpoint, int(actual))
    result.update(checkpoint=str(checkpoint), threshold_percent=draft.threshold_percent, target=draft.target_copies)
    history = detail(plan_id, session)
    result['actions'] = history['tasks'] + history['events']
    return result


@router.post('/plans/{plan_id}/correction')
def correction(plan_id: UUID, session: Session = Depends(get_session)):
    uid = Repository(session).user_id()
    session.execute(text('SELECT id FROM sb2_users WHERE id=:uid FOR UPDATE'), {'uid': uid})
    item = plan(session, uid, plan_id, True)
    state = monitor(plan_id, session)
    if state['status'] != 'below_threshold':
        raise HTTPException(409, 'Soglia non superata o dati insufficienti')
    # One proposal per checkpoint: retries cannot multiply corrections.
    marker = 'checkpoint:' + state['checkpoint']
    existing = session.execute(text('SELECT id FROM sb2_plans WHERE parent_id=:id AND brief LIKE :marker'), {'id': plan_id, 'marker': marker + '\n%'}).scalar()
    if existing:
        session.commit()
        return detail(existing, session)
    brief = marker + '\nProporre poche azioni correttive motivate entro il periodo originale. Non modificare il target originale.\n' + json.dumps({'original': item['draft'], 'monitor': state}, default=str, ensure_ascii=False)
    child = session.execute(text('''INSERT INTO sb2_plans(user_id,book_id,parent_id,brief) VALUES(:uid,:book_id,:parent_id,:brief) RETURNING id'''), {'uid': uid, 'book_id': item['book_id'], 'parent_id': plan_id, 'brief': brief}).scalar_one()
    session.commit()
    return detail(child, session)


@router.post('/plans/{plan_id}/regenerate')
def regenerate(plan_id: UUID, payload: RevisionInput, session: Session = Depends(get_session)):
    uid = Repository(session).user_id()
    original = plan(session, uid, plan_id, True)
    if original['status'] not in ('discarded','cleaned') or original['revision'] != payload.revision:
        raise HTTPException(409, 'Scartare o pulire il piano prima di ricominciare')
    source(session, uid, original)
    new_id = session.execute(text("""INSERT INTO sb2_plans(user_id,case_id,book_id,parent_id,brief,dialogue)
        VALUES(:uid,:case_id,:book_id,:parent_id,:brief,CAST(:dialogue AS jsonb)) RETURNING id"""),
        {'uid':uid,'case_id':original['case_id'],'book_id':original['book_id'],'parent_id':original['parent_id'],
         'brief':original['brief'],'dialogue':json.dumps(original['dialogue'])}).scalar_one()
    session.commit()
    return detail(new_id, session)


@router.get('/financial-events')
def financial_events(start: date, end: date, session: Session = Depends(get_session)):
    if end < start:
        raise HTTPException(422, 'Intervallo non valido')
    uid=Repository(session).user_id()
    return rows(session.execute(text('''SELECT t.id,t.transaction_date,t.description,t.amount,t.status,a.display_name AS account_name
        FROM sb2_transactions t JOIN sb2_accounts a ON a.id=t.account_id
        WHERE t.user_id=:uid AND a.user_id=:uid AND t.status='planned'
        AND t.transaction_date BETWEEN :start AND :end ORDER BY t.transaction_date,t.description'''),
        {'uid':uid,'start':start,'end':end}))


@router.post('/case-proposals/{message_id}/confirm')
def confirm_case_proposal(message_id: UUID, session: Session = Depends(get_session)):
    uid=Repository(session).user_id()
    session.execute(text('SELECT id FROM sb2_users WHERE id=:uid FOR UPDATE'),{'uid':uid})
    message=session.execute(text('''SELECT m.metadata_json FROM sb2_messages m JOIN sb2_conversations c ON c.id=m.conversation_id
        WHERE m.id=:id AND c.user_id=:uid AND m.role='assistant' FOR UPDATE OF m'''),{'id':message_id,'uid':uid}).scalar_one_or_none()
    if message is None:
        raise HTTPException(404,'Proposta non trovata')
    metadata=json.loads(message) if isinstance(message,str) else message
    result=metadata.get('result',{})
    if result.get('kind')!='case_proposal':
        raise HTTPException(409,'Il messaggio non contiene una proposta di pratica')
    data=result.get('data',{})
    if data.get('case_id'):
        return owned_case(session,uid,UUID(data['case_id']))
    title=data.get('title','').strip()
    if not title or len(title)>250:
        raise HTTPException(422,'Titolo non valido')
    existing=session.execute(text('SELECT id FROM sb2_cases WHERE user_id=:uid AND lower(title)=lower(:title) ORDER BY created_at LIMIT 1'),{'uid':uid,'title':title}).scalar_one_or_none()
    if existing:
        case_id=existing
    else:
        from uuid import uuid4
        case_id=session.execute(text('''INSERT INTO sb2_cases(user_id,code,title,status,context_markdown)
            VALUES(:uid,:code,:title,'active',:context) RETURNING id'''),{'uid':uid,'code':'PRATICA_'+uuid4().hex[:12].upper(),'title':title,'context':data.get('context_markdown','')}).scalar_one()
    data['case_id']=str(case_id)
    session.execute(text('UPDATE sb2_messages SET metadata_json=:metadata WHERE id=:id'),{'id':message_id,'metadata':json.dumps(metadata,ensure_ascii=False)})
    session.commit()
    return owned_case(session,uid,case_id)


from pydantic import BaseModel, Field

class StockPurchase(BaseModel):
    book_code: str
    purchase_date: date
    quantity: int = Field(gt=0)


def stock_book(session, uid, code):
    bid = session.execute(text("SELECT b.id FROM sb2_books b JOIN sb2_author_profiles a ON a.id=b.author_profile_id WHERE a.user_id=:uid AND b.code=:code FOR UPDATE OF b"), {"uid": uid, "code": code}).scalar_one_or_none()
    if bid is None:
        raise HTTPException(404, "Libro non trovato")
    return bid

@router.get('/inventory')
def inventory(session: Session = Depends(get_session)):
    uid = Repository(session).user_id()
    items = rows(session.execute(text("SELECT b.code,b.title,COALESCE(p.quantity,0) AS purchased,COALESCE(s.quantity,0) AS sold,COALESCE(p.quantity,0)-COALESCE(s.quantity,0) AS available FROM sb2_books b JOIN sb2_author_profiles a ON a.id=b.author_profile_id LEFT JOIN LATERAL (SELECT SUM(quantity) AS quantity FROM sb2_stock_purchases WHERE book_id=b.id) p ON true LEFT JOIN LATERAL (SELECT SUM(quantity) AS quantity FROM sb2_sales WHERE book_id=b.id AND from_inventory) s ON true WHERE a.user_id=:uid ORDER BY b.title"), {"uid":uid}))
    purchases = rows(session.execute(text("SELECT p.id,b.title,p.purchase_date,p.quantity FROM sb2_stock_purchases p JOIN sb2_books b ON b.id=p.book_id JOIN sb2_author_profiles a ON a.id=b.author_profile_id WHERE p.user_id=:uid AND a.user_id=:uid ORDER BY p.purchase_date DESC,p.created_at DESC"), {"uid":uid}))
    return {"items":items,"purchases":purchases}

@router.post('/inventory')
def purchase_stock(payload: StockPurchase, session: Session = Depends(get_session)):
    uid=Repository(session).user_id()
    bid=stock_book(session,uid,payload.book_code)
    session.execute(text("INSERT INTO sb2_stock_purchases(user_id,book_id,purchase_date,quantity) VALUES(:uid,:bid,:day,:quantity)"), {"uid":uid,"bid":bid,"day":payload.purchase_date,"quantity":payload.quantity})
    session.commit()
    return {"status":"created"}

@router.delete('/inventory/{purchase_id}')
def delete_stock(purchase_id: UUID, session: Session = Depends(get_session)):
    uid=Repository(session).user_id()
    purchase=session.execute(text("SELECT p.*,b.code FROM sb2_stock_purchases p JOIN sb2_books b ON b.id=p.book_id JOIN sb2_author_profiles a ON a.id=b.author_profile_id WHERE p.id=:id AND p.user_id=:uid AND a.user_id=:uid"), {"id":purchase_id,"uid":uid}).mappings().one_or_none()
    if purchase is None:
        raise HTTPException(404,"Acquisto non trovato")
    bid=stock_book(session,uid,purchase['code'])
    balance=session.execute(text("SELECT COALESCE((SELECT SUM(quantity) FROM sb2_stock_purchases WHERE book_id=:bid),0)-COALESCE((SELECT SUM(quantity) FROM sb2_sales WHERE book_id=:bid AND from_inventory),0)"), {"bid":bid}).scalar_one()
    if balance < purchase['quantity']:
        raise HTTPException(422,"Prima correggi le vendite: eliminando questo acquisto la giacenza diventerebbe negativa")
    session.execute(text("DELETE FROM sb2_stock_purchases WHERE id=:id"), {"id":purchase_id})
    session.commit()
    return {"status":"deleted"}
