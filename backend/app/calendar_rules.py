from datetime import datetime
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session


_EVENTS_TO_TODOS = """
    WITH expired_events AS (
        UPDATE sb2_events
        SET status='completed',updated_at=CURRENT_TIMESTAMP
        WHERE user_id=:uid AND status NOT IN ('completed','cancelled')
          AND event_date<:today
          AND ({condition})
        RETURNING id,user_id,project_id,case_id,author_profile_id,book_id,strategy_id,title
    )
    INSERT INTO sb2_tasks(
        user_id,project_id,case_id,author_profile_id,book_id,strategy_id,
        title,description,status,priority,due_date,due_time,source
    )
    SELECT
        e.user_id,e.project_id,e.case_id,e.author_profile_id,e.book_id,e.strategy_id,
        e.title,'calendar_event:' || e.id::text,'open',3,NULL,NULL,'calendar_rollover'
    FROM expired_events e
    WHERE NOT EXISTS (
          SELECT 1 FROM sb2_tasks t
          WHERE t.user_id=e.user_id
            AND t.description='calendar_event:' || e.id::text
            AND t.source='calendar_rollover'
      )
    ON CONFLICT DO NOTHING
"""


def _events_to_todos(session: Session, user_id: UUID, today, condition: str) -> int:
    """Chiude gli eventi passati che soddisfano `condition` e crea un TODO senza data
    per ciascuno. L'UPDATE ... RETURNING rende il rollover atomico: richieste
    simultanee non possono convertire due volte lo stesso evento.
    `condition` è sempre una costante del codice, mai input dell'utente."""
    result = session.execute(
        text(_EVENTS_TO_TODOS.format(condition=condition)),
        {"uid": user_id, "today": today},
    )
    return result.rowcount


def convert_past_project_book_events(session: Session, user_id: UUID, now: datetime) -> int:
    """Conversione eseguita all'avvio: ogni evento passato ancora aperto collegato a un
    progetto o a un libro (con o senza orario) viene chiuso e diventa un TODO senza data
    con gli stessi collegamenti. Gli eventi generati da piani o strategie sono esclusi:
    il monitoraggio li usa per segnalare i ritardi. Restituisce i TODO creati."""
    created = _events_to_todos(
        session, user_id, now.date(),
        "(project_id IS NOT NULL OR book_id IS NOT NULL) AND plan_id IS NULL AND strategy_id IS NULL",
    )
    session.commit()
    return created


def apply_calendar_rules(session: Session, user_id: UUID, now: datetime) -> None:
    """Apply predictable calendar housekeeping without involving the LLM."""
    today = now.date()

    session.execute(text("""
        UPDATE sb2_tasks
        SET due_date=NULL,status='open',updated_at=CURRENT_TIMESTAMP
        WHERE user_id=:uid AND status NOT IN ('completed','cancelled')
          AND due_date<:today AND due_time IS NULL
          AND num_nonnulls(strategy_id,plan_id,project_id,case_id,book_id)=0
    """), {"uid": user_id, "today": today})

    # Un evento senza orario rappresenta un'attività giornaliera. Se scade,
    # diventa un TODO senza data conservando gli eventuali collegamenti.
    # Gli eventi passati di una pratica (con o senza orario) non vanno persi:
    # diventano TODO collegati alla pratica. Gli eventi generati da un
    # piano/strategia restano gestiti dal modulo di pianificazione.
    _events_to_todos(session, user_id, today, """
        (start_time IS NULL
         AND num_nonnulls(strategy_id,plan_id,project_id,case_id,book_id)=0)
     OR (case_id IS NOT NULL AND plan_id IS NULL AND strategy_id IS NULL)
    """)

    session.execute(text("""
        UPDATE sb2_tasks
        SET status='completed',completed_at=CURRENT_TIMESTAMP,updated_at=CURRENT_TIMESTAMP
        WHERE user_id=:uid AND status NOT IN ('completed','cancelled')
          AND due_time IS NOT NULL
          AND due_date<:today
          AND num_nonnulls(strategy_id,plan_id,project_id,case_id,book_id)=0
    """), {"uid": user_id, "today": today})

    session.execute(text("""
        UPDATE sb2_events
        SET status='completed',updated_at=CURRENT_TIMESTAMP
        WHERE user_id=:uid AND status NOT IN ('completed','cancelled')
          AND start_time IS NOT NULL
          AND event_date<:today
          AND num_nonnulls(strategy_id,plan_id,project_id,case_id,book_id)=0
    """), {"uid": user_id, "today": today})
    session.commit()
