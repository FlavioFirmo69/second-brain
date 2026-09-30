from datetime import date as Date, time
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, Field, model_validator


class CaseInput(BaseModel):
    code: str = Field(min_length=1, max_length=80, pattern=r'^[A-Za-z0-9_-]+$')
    title: str = Field(min_length=1, max_length=250)
    context_markdown: str = ''


class PlanInput(BaseModel):
    case_id: UUID | None = None
    book_id: UUID | None = None
    brief: str = Field(min_length=1)

    @model_validator(mode='after')
    def context_required(self):
        if (self.case_id is None) == (self.book_id is None):
            raise ValueError('Selezionare una pratica oppure un libro')
        return self


class TurnInput(BaseModel):
    text: str = Field(min_length=1)
    revision: int


class RevisionInput(BaseModel):
    revision: int


class ProposedAction(BaseModel):
    kind: Literal['task', 'event'] = 'task'
    title: str = Field(min_length=1, max_length=500)
    reason: str = Field(min_length=1)
    expected_result: str = ''
    depends_on: list[int] = Field(default_factory=list)
    date: Date | None = None
    start_time: time | None = None
    end_time: time | None = None
    location: str | None = Field(default=None, max_length=500)
    priority: int = Field(default=3, ge=1, le=5)

    @model_validator(mode='after')
    def valid_schedule(self):
        if self.kind == 'event' and self.date is None:
            raise ValueError('Un evento richiede una data')
        if self.start_time and not self.date:
            raise ValueError('Un orario richiede una data')
        if self.end_time and (not self.start_time or self.end_time <= self.start_time):
            raise ValueError('Intervallo orario non valido')
        return self


class Milestone(BaseModel):
    date: Date
    cumulative_copies: int = Field(ge=0)


class Draft(BaseModel):
    title: str = Field(min_length=1, max_length=250)
    explanation: str = Field(min_length=1)
    assumptions: list[str] = Field(default_factory=list)
    actions: list[ProposedAction] = Field(min_length=1, max_length=100)
    start_date: Date
    end_date: Date
    target_copies: int | None = Field(default=None, gt=0)
    threshold_percent: float = Field(default=30, gt=0, le=100)
    threshold_reason: str = Field(min_length=1)
    minimum_expected: int = Field(default=20, ge=1)
    milestones: list[Milestone] = Field(default_factory=list)

    @model_validator(mode='after')
    def coherent(self):
        if self.end_date < self.start_date:
            raise ValueError('Periodo non valido')
        for index, action in enumerate(self.actions):
            if any(dep < 0 or dep >= index for dep in action.depends_on):
                raise ValueError('Le dipendenze devono riferirsi ad azioni precedenti (indice da zero)')
            if action.date and not self.start_date <= action.date <= self.end_date:
                raise ValueError('Attività fuori dal periodo del piano')
        previous_date, previous_copies = None, 0
        for point in self.milestones:
            if not self.start_date <= point.date <= self.end_date or (previous_date and point.date <= previous_date) or point.cumulative_copies < previous_copies:
                raise ValueError('Aspettative cumulative non coerenti')
            previous_date, previous_copies = point.date, point.cumulative_copies
        if self.target_copies is not None:
            if not self.milestones or self.milestones[-1].date != self.end_date or self.milestones[-1].cumulative_copies != self.target_copies:
                raise ValueError('L’ultimo punto deve coincidere con target e fine periodo')
        return self


class DraftInput(BaseModel):
    revision: int
    draft: Draft


class CoverageInput(BaseModel):
    through: Date
