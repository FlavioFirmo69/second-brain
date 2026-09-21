from datetime import datetime
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session


def apply_calendar_rules(session: Session, user_id: UUID, now: datetime) -> None:
    """Apply predictable calendar housekeeping without involving the LLM."""
    today = now.date()
    current_time = now.time().replace(microsecond=0)

    session.execute(text("""
        UPDATE sb2_tasks
        SET due_date=NULL,status='open',updated_at=CURRENT_TIMESTAMP
        WHERE user_id=:uid AND status NOT IN ('completed','cancelled')
          AND due_date<:today AND due_time IS NULL
    """), {"uid": user_id, "today": today})

    session.execute(text("""
        UPDATE sb2_tasks
        SET status='completed',completed_at=CURRENT_TIMESTAMP,updated_at=CURRENT_TIMESTAMP
        WHERE user_id=:uid AND status NOT IN ('completed','cancelled')
          AND due_time IS NOT NULL
          AND (due_date<:today OR (due_date=:today AND due_time<:current_time))
    """), {"uid": user_id, "today": today, "current_time": current_time})

    session.execute(text("""
        UPDATE sb2_events
        SET status='completed',updated_at=CURRENT_TIMESTAMP
        WHERE user_id=:uid AND status NOT IN ('completed','cancelled')
          AND start_time IS NOT NULL
          AND (event_date<:today OR (event_date=:today AND start_time<:current_time))
    """), {"uid": user_id, "today": today, "current_time": current_time})
    session.commit()
