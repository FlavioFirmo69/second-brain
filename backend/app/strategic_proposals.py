"""Dated suggestions and user decisions, stored in the existing chat/diary only."""
import json
from datetime import date
from typing import Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import text
from sqlalchemy.orm import Session
from .database import get_session
from .repository import Repository

router = APIRouter()

PROPOSAL_FORMAT = '''Restituisci JSON con questa struttura:
{"answer":"risposta in Markdown per l'utente", "proposals":[{"action":"primo passo concreto",
"proposed_date":"YYYY-MM-DD", "rationale":"perché è utile e perché quella data",
"source_refs":["strategies:identificativo-ufficiale"]}]}.
L'answer contiene il ragionamento; le proposte appariranno anche come schede con Accetta e Rifiuta.
Massimo tre proposte, soltanto se fondate e utili: se non ne emergono usa proposals: [].
Per una opportunità concreta suggerisci una data non passata a partire dalla data corrente del
contesto e dalle occasioni note: se l'incontro è datato proponi quel giorno, altrimenti una data
indicativa ragionevole, motivandola e dichiarando che è da concordare. Non inventare date di eventi
o disponibilità delle persone. La data è un obiettivo per un primo contatto o una verifica, non un
appuntamento già fissato. Usa riferimenti ufficiali esistenti per sostenere il collegamento;
non inventarli. Per proposte editoriali collega la strategia attiva pertinente con un riferimento
strategies:ID, non soltanto il libro o il profilo autore. Cesare è un profilo: identifica la sua
strategia attiva coerente con l'opportunità, non una strategia di un altro autore. Se più strategie
sono plausibili e mancano elementi per scegliere, chiedi un chiarimento senza inventare il legame.
Una scheda proposta non è accettata né registrata come decisione nel diario: l'utente deve scegliere.
Le decisioni già accettate o rifiutate sono riportate nel diario: considerane la motivazione prima
di riproporre lo stesso passo. Un rifiuto circoscritto non è una preferenza permanente generale.
La sola appartenenza a un'azienda non dimostra ruolo, interesse o idoneità come testimonial.
Non inserire UUID o nomi tecnici nell'answer, nell'action o nella rationale.'''


class DatedProposal(BaseModel):
    action: str = Field(min_length=3, max_length=1000)
    proposed_date: date
    rationale: str = Field(min_length=3, max_length=1500)
    source_refs: list[str] = Field(min_length=1, max_length=20)


def strategy_links(sources, refs):
    """Readable labels derived from official records; IDs remain the actual link."""
    profiles = {str(row['id']):row for row in sources.get('author_profiles', [])}
    books = {str(row['id']):row for row in sources.get('books', [])}
    selected = {ref.split(':',1)[1] for ref in refs if ref.startswith('strategies:')}
    links = []
    for row in sources.get('strategies', []):
        if str(row['id']) not in selected:continue
        book = books.get(str(row.get('book_id')), {})
        author = profiles.get(str(row.get('author_profile_id') or book.get('author_profile_id')), {})
        links.append({'id':str(row['id']), 'title':row.get('title') or row.get('code') or 'Strategia',
                      'author_name':author.get('display_name') or author.get('code') or '',
                      'book_title':book.get('title') or ''})
    return links


def parse_advice(raw, context):
    """Legacy text stays readable; only valid, grounded suggestions become clickable."""
    try:
        value = json.loads(raw)
    except (ValueError, TypeError):
        return raw, []
    if not isinstance(value, dict) or not isinstance(value.get('answer'), str) or not value['answer'].strip():
        return raw, []
    today = date.fromisoformat(str(context['date'])[:10])
    refs = {f'{source}:{row["id"]}' for source, items in context['sources'].items()
            for row in items if row.get('id') is not None and
            (source != 'strategies' or row.get('status') == 'active')}
    proposals = []
    candidates = value.get('proposals', [])
    for candidate in candidates[:3] if isinstance(candidates, list) else []:
        try:
            item = DatedProposal.model_validate(candidate)
        except ValidationError:
            continue
        if not item.action.strip() or not item.rationale.strip() or item.proposed_date < today:
            continue
        if any(ref not in refs for ref in item.source_refs):
            continue
        links = strategy_links(context['sources'], item.source_refs)
        if not links and any(ref.startswith(('books:', 'author_profiles:', 'channels:', 'book_editions:')) for ref in item.source_refs):
            # An author or book is not itself a strategy.
            continue
        proposals.append({'id':str(uuid4()), **item.model_dump(mode='json'), 'status':'proposed',
                          'strategy_ids':[link['id'] for link in links], 'strategy_links':links})
    return value['answer'], proposals


class ProposalDecision(BaseModel):
    decision: Literal['accepted', 'rejected']
    reason: str = Field(default='', max_length=2000)
    planned_date: date | None = None


@router.post('/proposals/{message_id}/{proposal_id}/decision')
def decide_proposal(message_id: UUID, proposal_id: UUID, payload: ProposalDecision,
                    session: Session = Depends(get_session)):
    repo = Repository(session)
    uid = repo.user_id()
    reason = payload.reason.strip()
    if payload.decision == 'rejected' and not reason:
        raise HTTPException(422, 'Per rifiutare la proposta indica una motivazione.')
    # Serialize decisions and write both diary entry and state in a single transaction.
    row = session.execute(text('''SELECT m.conversation_id,m.metadata_json FROM sb2_messages m
        JOIN sb2_conversations c ON c.id=m.conversation_id
        WHERE m.id=:id AND c.user_id=:uid AND c.status='active'
          AND m.role='assistant' AND m.message_kind='strategic_advice'
        FOR UPDATE OF m'''), {'id':message_id,'uid':uid}).mappings().one_or_none()
    if row is None:
        raise HTTPException(404, 'Proposta non trovata')
    metadata = json.loads(row['metadata_json'] or '{}')
    proposal = next((p for p in metadata.get('strategic_proposals', []) if p['id']==str(proposal_id)), None)
    if proposal is None:
        raise HTTPException(404, 'Proposta non trovata')
    if proposal['status'] != 'proposed':
        if proposal['status'] == payload.decision:
            return {'proposal':proposal, 'already_recorded':True}
        raise HTTPException(409, 'Questa proposta ha già una decisione registrata nel diario.')
    planned = payload.planned_date or date.fromisoformat(proposal['proposed_date'])
    if payload.decision == 'accepted' and planned < date.fromisoformat(str(repo.today())[:10]):
        raise HTTPException(422, 'Scegli una data prevista da oggi in avanti.')
    ids = list(dict.fromkeys(ref.split(':',1)[1] for ref in proposal['source_refs'] if ref.startswith('strategies:')))
    links = proposal.get('strategy_links', [])
    if payload.decision == 'accepted':
        links = []
        for identity in ids:
            strategy = session.execute(text('''SELECT s.id,s.title,s.status,a.display_name AS author_name,b.title AS book_title
                FROM sb2_strategies s LEFT JOIN sb2_books b ON b.id=s.book_id
                LEFT JOIN sb2_author_profiles a ON a.id=COALESCE(s.author_profile_id,b.author_profile_id) AND a.user_id=s.user_id
                WHERE s.id=CAST(:strategy_id AS uuid) AND s.user_id=:uid FOR SHARE OF s'''),
                {'strategy_id':identity,'uid':uid}).mappings().one_or_none()
            if strategy is None or strategy['status'] != 'active':
                raise HTTPException(409, 'La strategia collegata non è più attiva o accessibile. Chiedi al consulente di aggiornare la proposta.')
            links.append({'id':str(strategy['id']),'title':strategy['title'],
                          'author_name':strategy['author_name'] or '', 'book_title':strategy['book_title'] or ''})
        if not ids and any(ref.startswith(('books:', 'author_profiles:', 'channels:', 'book_editions:')) for ref in proposal['source_refs']):
            raise HTTPException(409, 'La proposta editoriale non indica una strategia. Chiedi al consulente di precisare il collegamento.')
    strategy_note = ''.join('\nStrategia collegata: '+link['title']+
                            (' · '+link['author_name'] if link.get('author_name') else '')+
                            (' · '+link['book_title'] if link.get('book_title') else '') for link in links)
    if payload.decision == 'accepted':
        content = ('Decisione strategica accettata\n\n'+proposal['action']+
                   '\nData prevista: '+planned.strftime('%d/%m/%Y')+strategy_note+
                   '\nMotivo della proposta: '+proposal['rationale']+
                   ('\nNota dell’utente: '+reason if reason else '')+
                   '\nÈ un’intenzione concordata, non un’azione già eseguita né un appuntamento confermato.')
    else:
        content = ('Proposta strategica rifiutata\n\n'+proposal['action']+
                   '\nData proposta: '+date.fromisoformat(proposal['proposed_date']).strftime('%d/%m/%Y')+strategy_note+
                   '\nMotivazione dell’utente: '+reason+
                   '\nIl rifiuto riguarda questa proposta; non implica una preferenza generale permanente.')
    diary_metadata = {'strategic_decision':{'message_id':str(message_id),'proposal_id':str(proposal_id),
                                          'decision':payload.decision,'source_refs':proposal['source_refs'],
                                          'strategy_ids':ids, 'planned_date':planned.isoformat() if payload.decision=='accepted' else None}}
    entry = session.execute(text('''INSERT INTO sb2_messages(conversation_id,role,content_markdown,message_kind,metadata_json)
        VALUES(:cid,'user',:content,'strategic_diary',:metadata) RETURNING id'''),
        {'cid':row['conversation_id'],'content':content,'metadata':json.dumps(diary_metadata,ensure_ascii=False)}).scalar_one()
    proposal.update(status=payload.decision, reason=reason, diary_entry_id=str(entry), strategy_ids=ids, strategy_links=links)
    if payload.decision == 'accepted':
        proposal['planned_date'] = planned.isoformat()
    session.execute(text('UPDATE sb2_messages SET metadata_json=:metadata WHERE id=:id'),
                    {'id':message_id,'metadata':json.dumps(metadata,ensure_ascii=False)})
    session.execute(text('UPDATE sb2_conversations SET updated_at=CURRENT_TIMESTAMP WHERE id=:cid AND user_id=:uid'),
                    {'cid':row['conversation_id'],'uid':uid})
    session.commit()
    return {'proposal':proposal,'already_recorded':False}
