from datetime import date, timedelta
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from .assistant import answer
from .database import get_session
from .repository import Repository
from .schemas import AssistantRequest, BalanceCreate, BookUpdate, ConversationCreate, EventCreate, InboxCreate, ProfileUpdate, ProjectAssignment, ProjectCreate, SaleCreate, TaskCreate, TaskSchedule, TransactionCreate
from .version import APP_VERSION

router = APIRouter(prefix="/api")
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def repo(session: Session = Depends(get_session)) -> Repository:
    return Repository(session)


@router.get("/health")
def health(session: Session = Depends(get_session)):
    try:
        session.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database non disponibile: {exc.__class__.__name__}") from exc


@router.get("/system/info")
def system_info(repository: Repository = Depends(repo)):
    return {
        "version": APP_VERSION,
        "environment": repository.settings.app_env,
        "llm_enabled": repository.settings.llm_enabled,
        "llm_model": repository.settings.llm_model or None,
    }


@router.get("/dashboard/today")
def dashboard_today(repository: Repository = Depends(repo)):
    return repository.dashboard()


@router.get("/dashboard/week")
def dashboard_week(repository: Repository = Depends(repo)):
    return repository.week()


@router.get("/tasks")
def list_tasks(repository: Repository = Depends(repo)):
    return repository.list_tasks()


@router.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, repository: Repository = Depends(repo)):
    return repository.create_task(payload.model_dump())


@router.post("/tasks/{task_id}/complete", status_code=status.HTTP_204_NO_CONTENT)
def complete_task(task_id: UUID, repository: Repository = Depends(repo)):
    try:
        repository.complete_task(task_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/tasks/{task_id}/schedule")
def schedule_task(task_id: UUID, payload: TaskSchedule, repository: Repository = Depends(repo)):
    try:
        return repository.schedule_task(task_id, payload.due_date, payload.due_time)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/tasks/{task_id}/context")
def assign_task_context(task_id: UUID, payload: ProjectAssignment, repository: Repository = Depends(repo)):
    try:
        return repository.assign_context("task", task_id, payload.project_id, payload.case_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/events")
def list_events(
    start: date = Query(default_factory=date.today),
    end: date | None = None,
    repository: Repository = Depends(repo),
):
    return repository.list_events(start, end or start + timedelta(days=90))


@router.post("/events", status_code=status.HTTP_201_CREATED)
def create_event(payload: EventCreate, repository: Repository = Depends(repo)):
    return repository.create_event(payload.model_dump())


@router.put("/events/{event_id}")
def update_event(event_id: UUID, payload: EventCreate, repository: Repository = Depends(repo)):
    try:
        return repository.update_event(event_id, payload.model_dump())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/events/{event_id}/context")
def assign_event_context(event_id: UUID, payload: ProjectAssignment, repository: Repository = Depends(repo)):
    try:
        return repository.assign_context("event", event_id, payload.project_id, payload.case_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/events/{event_id}/complete", status_code=status.HTTP_204_NO_CONTENT)
def complete_event(event_id: UUID, repository: Repository = Depends(repo)):
    try:
        repository.complete_event(event_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: UUID, repository: Repository = Depends(repo)):
    try:
        repository.delete_event(event_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/profiles")
def profiles(repository: Repository = Depends(repo)):
    return repository.profiles()


@router.put("/profiles/{code}")
def update_profile(code: str, payload: ProfileUpdate, repository: Repository = Depends(repo)):
    try:
        return repository.update_profile(code, payload.model_dump())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/strategies")
def strategies(repository: Repository = Depends(repo)):
    return repository.strategies()


@router.get("/books")
def books(repository: Repository = Depends(repo)):
    return repository.books()


@router.put("/books/{book_id}")
def update_book(book_id: UUID, payload: BookUpdate, repository: Repository = Depends(repo)):
    try:
        return repository.update_book(book_id, payload.model_dump())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/projects")
def projects(repository: Repository = Depends(repo)):
    return repository.projects()


@router.post("/projects", status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, repository: Repository = Depends(repo)):
    try:
        return repository.create_project(payload.model_dump())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/cases")
def cases(repository: Repository = Depends(repo)):
    return repository.cases()


@router.get("/sales")
def sales(book_code: str | None = None, repository: Repository = Depends(repo)):
    return repository.sales_progress(book_code)


@router.post("/sales", status_code=status.HTTP_201_CREATED)
def create_sale(payload: SaleCreate, repository: Repository = Depends(repo)):
    try:
        return repository.add_sale(payload.model_dump())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/finance")
def finance(repository: Repository = Depends(repo)):
    return repository.finance()


@router.post("/finance/balance", status_code=status.HTTP_201_CREATED)
def set_balance(payload: BalanceCreate, repository: Repository = Depends(repo)):
    try:
        return repository.set_balance(payload.model_dump())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/finance/transactions", status_code=status.HTTP_201_CREATED)
def create_transaction(payload: TransactionCreate, repository: Repository = Depends(repo)):
    try:
        return repository.create_transaction(payload.model_dump())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/inbox")
def inbox(repository: Repository = Depends(repo)):
    return repository.inbox()


@router.post("/inbox", status_code=status.HTTP_201_CREATED)
def add_inbox(payload: InboxCreate, repository: Repository = Depends(repo)):
    return repository.add_inbox(payload.text, payload.source)


@router.delete("/inbox/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inbox(item_id: UUID, repository: Repository = Depends(repo)):
    try:
        repository.delete_inbox(item_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/inbox/{item_id}/execute")
async def execute_inbox(item_id: UUID, session: Session = Depends(get_session)):
    repository = Repository(session)
    try:
        item = repository.inbox_item(item_id)
        if item["status"] != "new" or not repository.can_execute_inbox(item["text"]):
            raise HTTPException(status_code=409, detail="Questo comando non può essere eseguito automaticamente")
        result = await answer(session, item["text"])
        if result.get("kind") not in {"event_created", "events_created", "task_created", "tasks_created", "sales"}:
            raise HTTPException(status_code=409, detail="Il comando non ha prodotto un'azione eseguibile")
        repository.complete_inbox(item_id, result)
        return result
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/commands")
def commands(repository: Repository = Depends(repo)):
    return repository.commands()


@router.get("/manuals/deterministic-rules")
def deterministic_rules():
    path = PROJECT_ROOT / "config" / "manuals" / "regole-deterministiche.md"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Manuale delle regole non trovato")
    return {"content_markdown": path.read_text(encoding="utf-8")}


@router.post("/assistant")
async def assistant(payload: AssistantRequest, session: Session = Depends(get_session)):
    return await answer(session, payload.text)


@router.get("/conversations")
def conversations(repository: Repository = Depends(repo)):
    return repository.list_conversations()


@router.post("/conversations", status_code=status.HTTP_201_CREATED)
def create_conversation(payload: ConversationCreate, repository: Repository = Depends(repo)):
    return repository.create_conversation(payload.title)


@router.get("/conversations/{conversation_id}/messages")
def conversation_messages(conversation_id: UUID, repository: Repository = Depends(repo)):
    return repository.conversation_messages(conversation_id)


@router.post("/conversations/{conversation_id}/messages", status_code=status.HTTP_201_CREATED)
async def create_conversation_message(conversation_id: UUID, payload: AssistantRequest, session: Session = Depends(get_session)):
    repository = Repository(session)
    try:
        history = [{"role": item["role"], "content": item["content_markdown"]}
                   for item in repository.conversation_messages(conversation_id)]
        user_message = repository.add_conversation_message(conversation_id, "user", payload.text)
        result = await answer(session, payload.text, history)
        data = result.get("data") or {}
        summaries = {
            "dashboard": "Ecco le attività e gli eventi di oggi.",
            "week": "Ecco gli impegni della settimana.",
            "finance": "Ecco il saldo e i movimenti pianificati.",
            "commands": "Ecco i comandi disponibili.",
            "calendar_query": "Ecco i risultati trovati nel calendario.",
        }
        content = data.get("content_markdown") if result.get("kind") == "article" else result.get("message") or data.get("text") or summaries.get(result.get("kind"), "Richiesta elaborata.")
        metadata = data if result.get("kind") == "article" else {"result": result}
        assistant_message = repository.add_conversation_message(conversation_id, "assistant", content, result.get("kind", "text"), metadata)
        return {"conversation_id": conversation_id, "user_message": user_message,
                "assistant_message": assistant_message, "result": result}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
