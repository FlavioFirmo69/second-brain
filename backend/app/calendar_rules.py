from datetime import datetime
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session


def apply_calendar_rules(session: Session, user_id: UUID, now: datetime) -> None:
    """Apply predictable calendar housekeeping without involving the LLM."""
    today = now.date()

    session.execute(text("""
        UPDATE sb2_tasks
        SET due_date=NULL,status='open',updated_at=CURRENT_TIMESTAMP
        WHERE user_id=:uid AND status NOT IN ('completed','cancelled')
          AND due_date<:today AND due_time IS NULL
    """), {"uid": user_id, "today": today})

    # Un evento senza orario rappresenta un'attività giornaliera. Se scade,
    # diventa un TODO senza data conservando gli eventuali collegamenti.
    session.execute(text("""
        INSERT INTO sb2_tasks(
            user_id,project_id,case_id,author_profile_id,book_id,
            title,description,status,priority,due_date,due_time,source
        )
        SELECT
            e.user_id,e.project_id,e.case_id,e.author_profile_id,e.book_id,
            e.title,'calendar_event:' || e.id::text,'open',3,NULL,NULL,'calendar_rollover'
        FROM sb2_events e
        WHERE e.user_id=:uid
          AND e.status NOT IN ('completed','cancelled')
          AND e.event_date<:today
          AND e.start_time IS NULL
          AND NOT EXISTS (
              SELECT 1 FROM sb2_tasks t
              WHERE t.user_id=e.user_id
                AND t.description='calendar_event:' || e.id::text
                AND t.source='calendar_rollover'
          )
    """), {"uid": user_id, "today": today})

    session.execute(text("""
        UPDATE sb2_events
        SET status='completed',updated_at=CURRENT_TIMESTAMP
        WHERE user_id=:uid AND status NOT IN ('completed','cancelled')
          AND event_date<:today AND start_time IS NULL
    """), {"uid": user_id, "today": today})

    session.execute(text("""
        UPDATE sb2_tasks
        SET status='completed',completed_at=CURRENT_TIMESTAMP,updated_at=CURRENT_TIMESTAMP
        WHERE user_id=:uid AND status NOT IN ('completed','cancelled')
          AND due_time IS NOT NULL
          AND due_date<:today
    """), {"uid": user_id, "today": today})

    session.execute(text("""
        UPDATE sb2_events
        SET status='completed',updated_at=CURRENT_TIMESTAMP
        WHERE user_id=:uid AND status NOT IN ('completed','cancelled')
          AND start_time IS NOT NULL
          AND event_date<:today
    """), {"uid": user_id, "today": today})
    session.commit()
