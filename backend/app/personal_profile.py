"""The user's editable, authoritative cross-domain goals document."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import text
from sqlalchemy.orm import Session
from .database import get_session
from .repository import Repository

router = APIRouter(prefix='/api/personal-profile', tags=['Profilo personale'])

TEMPLATE = '''# Profilo personale e desideri

## Direzione generale

## Lavoro dipendente: ruolo desiderato e confini

## Scrittura indipendente: visione e priorità

## Consulenze: obiettivi e criteri di scelta

## Tempo personale, relazioni e autonomia

## Vincoli e compromessi accettabili

## Cosa evitare e quando dire di no
'''

def current_profile(session, uid):
    item = session.execute(text('SELECT id,content_markdown,revision,updated_at FROM sb2_personal_profiles WHERE user_id=:uid'),
                           {'uid': uid}).mappings().one_or_none()
    return dict(item) if item else None

@router.get('')
def read_profile(session: Session = Depends(get_session)):
    item = current_profile(session, Repository(session).user_id())
    return {**item, 'exists': True} if item else {
        'exists': False, 'id': None, 'content_markdown': TEMPLATE, 'revision': 0, 'updated_at': None}

class ProfileUpdate(BaseModel):
    content_markdown: str = Field(min_length=1, max_length=30000)
    revision: int = Field(ge=0)

    @field_validator('content_markdown')
    @classmethod
    def substantive_document(cls, value):
        if not value.strip():
            raise ValueError('Il documento non può essere vuoto')
        return value

@router.put('')
def save_profile(payload: ProfileUpdate, session: Session = Depends(get_session)):
    repo = Repository(session)
    uid = repo.user_id()
    session.execute(text('SELECT id FROM sb2_users WHERE id=:uid FOR UPDATE'), {'uid': uid})
    before = current_profile(session, uid)
    if payload.revision != (before['revision'] if before else 0):
        raise HTTPException(409, 'Il profilo è stato modificato altrove. Ricarica il documento prima di salvare.')
    if before:
        query = '''UPDATE sb2_personal_profiles SET content_markdown=:content,revision=revision+1,updated_at=now()
                   WHERE user_id=:uid RETURNING id,content_markdown,revision,updated_at'''
    else:
        query = '''INSERT INTO sb2_personal_profiles(user_id,content_markdown)
                   VALUES(:uid,:content) RETURNING id,content_markdown,revision,updated_at'''
    after = dict(session.execute(text(query), {'uid': uid, 'content': payload.content_markdown}).mappings().one())
    repo.log(uid, 'personal_profile', after['id'], 'update' if before else 'create', before, after)
    session.commit()
    return {**after, 'exists': True}
