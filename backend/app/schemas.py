from datetime import date, time
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    due_date: date | None = None
    due_time: time | None = None
    priority: int = Field(default=3, ge=1, le=5)
    project_id: UUID | None = None
    case_id: UUID | None = None
    author_profile_id: UUID | None = None
    book_id: UUID | None = None


class EventCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    event_date: date
    start_time: time | None = None
    end_time: time | None = None
    location: str | None = Field(default=None, max_length=500)
    event_type: str = Field(default="personal", max_length=40)
    project_id: UUID | None = None
    case_id: UUID | None = None
    author_profile_id: UUID | None = None
    book_id: UUID | None = None


class ProjectAssignment(BaseModel):
    project_id: UUID | None = None
    case_id: UUID | None = None


class InboxCreate(BaseModel):
    text: str = Field(min_length=1)
    source: str = Field(default="desktop", max_length=40)


class SaleCreate(BaseModel):
    book_code: str
    quantity: int = Field(gt=0)
    sale_date: date
    channel: str | None = None
    notes: str | None = None


class BalanceCreate(BaseModel):
    account_code: str = "ING_CURRENT"
    balance: Decimal
    balance_date: date
    notes: str | None = None


class ProfileUpdate(BaseModel):
    positioning: str
    voice_markdown: str
    privacy_markdown: str = ""
    change_reason: str = Field(min_length=1, max_length=500)


class AssistantRequest(BaseModel):
    text: str = Field(min_length=1)


class ConversationCreate(BaseModel):
    title: str = Field(default="Nuova conversazione", min_length=1, max_length=250)
