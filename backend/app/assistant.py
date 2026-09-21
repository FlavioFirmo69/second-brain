import json
import re
from datetime import date, time, timedelta

from sqlalchemy.orm import Session

from .llm import LlmUnavailable, complete
from .repository import Repository


def normalize(value: str) -> str:
    return " ".join(value.lower().strip().split())


MONTHS = {
    "gennaio": 1, "febbraio": 2, "marzo": 3, "aprile": 4, "maggio": 5, "giugno": 6,
    "luglio": 7, "agosto": 8, "settembre": 9, "ottobre": 10, "novembre": 11, "dicembre": 12,
}


def future_date(day: int, month: int, year: int | None, today: date) -> date:
    result = date(year or today.year, month, day)
    if year is None and result < today:
        result = date(today.year + 1, month, day)
    return result


async def answer(session: Session, raw_text: str, history: list[dict[str, str]] | None = None) -> dict:
    repo = Repository(session)
    command = normalize(raw_text)
    if command == "oggi":
        return {"mode": "deterministic", "kind": "dashboard", "data": repo.dashboard()}
    if command == "settimana":
        return {"mode": "deterministic", "kind": "week", "data": repo.week()}
    if command in {"saldo", "saldo e movimenti", "movimenti"}:
        return {"mode": "deterministic", "kind": "finance", "data": repo.finance()}
    if command == "comandi":
        return {"mode": "deterministic", "kind": "commands", "data": repo.commands()}
    if command.startswith("nota "):
        return {"mode": "deterministic", "kind": "inbox", "data": repo.add_inbox(raw_text[5:].strip(), "assistant")}
    todo = re.fullmatch(r"(?:todo\s*:|todo|aggiungi todo|da fare\s*:?)\s*(.+)", command)
    if todo:
        item = repo.create_task({
            "title": todo.group(1).strip().capitalize(), "due_date": None, "due_time": None,
            "priority": 3, "project_id": None, "case_id": None,
            "author_profile_id": None, "book_id": None,
        })
        return {"mode": "deterministic", "kind": "task_created", "data": item,
                "message": f"TODO creato: {item['title']}"}
    event = re.fullmatch(r"(?:stasera|oggi)(?:\s+(?:alle|ore))?\s+(\d{1,2})(?::(\d{2}))?\s+(.+)", command)
    if event:
        hour, minute, title = event.groups()
        item = repo.create_event({
            "title": title.strip().capitalize(), "event_date": repo.today(),
            "start_time": time(int(hour), int(minute or 0)), "end_time": None, "location": None,
            "event_type": "personal", "author_profile_id": None, "book_id": None,
        })
        return {"mode": "deterministic", "kind": "event_created", "data": item,
                "message": f"Evento creato oggi alle {int(hour):02d}:{int(minute or 0):02d}: {item['title']}"}
    event = re.fullmatch(r"domani(?:\s+(?:alle|ore))?\s+(\d{1,2})(?::(\d{2}))?\s+(.+)", command)
    if event:
        hour, minute, title = event.groups()
        item = repo.create_event({
            "title": title.strip().capitalize(), "event_date": repo.today() + timedelta(days=1),
            "start_time": time(int(hour), int(minute or 0)), "end_time": None, "location": None,
            "event_type": "personal", "author_profile_id": None, "book_id": None,
        })
        return {"mode": "deterministic", "kind": "event_created", "data": item,
                "message": f"Evento creato domani alle {int(hour):02d}:{int(minute or 0):02d}: {item['title']}"}
    absolute_event = re.fullmatch(
        r"(?:crea(?:\s+un)?\s+evento\s+)?(?:il\s+)?(\d{1,2})\s+"
        r"(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)"
        r"(?:\s+(\d{4}))?\s+(?:ore|alle)\s+(\d{1,2})(?::(\d{2}))?\s*[:,\-]?\s*(.+)",
        command,
    )
    if absolute_event:
        day, month_name, year, hour, minute, title = absolute_event.groups()
        event_date = future_date(int(day), MONTHS[month_name], int(year) if year else None, repo.today())
        item = repo.create_event({
            "title": title.strip().capitalize(), "event_date": event_date,
            "start_time": time(int(hour), int(minute or 0)), "end_time": None, "location": None,
            "event_type": "personal", "author_profile_id": None, "book_id": None,
        })
        return {"mode": "deterministic", "kind": "event_created", "data": item,
                "message": f"Evento creato il {event_date.strftime('%d/%m/%Y')} alle {int(hour):02d}:{int(minute or 0):02d}: {item['title']}"}
    match = re.fullmatch(r"ho venduto\s+(\d+)\s+copie\s+di\s+(.+)", command)
    if match:
        quantity, book = match.groups()
        return {
            "mode": "deterministic",
            "kind": "sales",
            "data": repo.add_sale({"book_code": book.strip(), "quantity": int(quantity), "sale_date": repo.today(), "channel": None, "notes": "Comando naturale"}),
        }

    profiles = repo.profiles()
    strategies = repo.strategies()
    projects = repo.projects()
    cases = repo.cases()
    context = "\n\n".join(
        [f"PROFILO {p['code']}:\n{p['positioning']}\n{p['voice_markdown']}\n{p['privacy_markdown']}" for p in profiles]
        + [f"STRATEGIA {s['code']}:\n{s['content_markdown']}" for s in strategies]
        + [f"PROGETTO {p['code']}: {p['title']}\n{p.get('objective') or ''}" for p in projects]
        + [f"PRATICA {c['code']}: {c['title']}\n{c.get('context_markdown') or ''}" for c in cases]
    )
    response = ""
    try:
        messages = [
            {"role": "system", "content": f"""Sei il Second Brain personale. Oggi è {repo.today().isoformat()}.
Usa solo il contesto pertinente e mantieni separate le identità autoriali.
Rispondi ESCLUSIVAMENTE con un oggetto JSON, senza markdown, scegliendo una forma:
{{"action":"create_event","title":"...","event_date":"YYYY-MM-DD","start_time":"HH:MM:SS o null","location":null,"event_type":"personal","project_code":null,"case_code":null}}
{{"action":"create_events","events":[{{"title":"...","event_date":"YYYY-MM-DD","start_time":"HH:MM:SS o null","end_time":"HH:MM:SS o null","location":null,"event_type":"personal","project_code":null,"case_code":null}}]}}
{{"action":"create_task","title":"...","due_date":"YYYY-MM-DD o null","due_time":"HH:MM:SS o null","priority":3,"project_code":"codice progetto o null","case_code":"codice pratica o null"}}
{{"action":"create_tasks","tasks":[{{"title":"...","due_date":"YYYY-MM-DD o null","due_time":"HH:MM:SS o null","priority":3,"project_code":null,"case_code":"codice pratica o null"}}]}}
{{"action":"respond","text":"..."}}
{{"action":"draft_article","title":"...","subtitle":"...","content_markdown":"...","author_code":"CESARE o FLAVIO"}}
Per un articolo destinato a Substack usa draft_article: titolo e sottotitolo separati, testo completo in Markdown pulito, paragrafi brevi, sottotitoli, elenchi solo se utili e nessun blocco di codice. Applica fedelmente la voce dell'autore richiesto.
Per gli impegni interpreta "entro le" e "prima delle" come scadenza di una create_task usando due_date e due_time. Interpreta "alle" come create_event quando la frase descrive un appuntamento o uno spostamento; usa create_task quando descrive qualcosa da fare o un promemoria. Risolvi oggi, domani e i giorni della settimana rispetto alla data odierna indicata sopra.
Quando l'utente fornisce un itinerario, un programma giornaliero o chiede di creare più elementi a calendario, usa create_events e restituisci un elemento per ogni tappa. Conserva gli intervalli con start_time ed end_time; per un orario puntuale usa end_time null. Non omettere trasferimenti, arrivi o partenze esplicitamente elencati.
Quando un'attività deriva da una strategia o riguarda chiaramente uno dei PROGETTI elencati, valorizza project_code con il relativo codice. Non indovinare collegamenti incerti: usa null. Le attività operative generate insieme a una strategia devono sempre riportare il project_code della strategia.
Quando l'utente elenca più azioni da fare usa create_tasks e crea un elemento per ogni azione. Se nomina una PRATICA, usa il suo codice esatto in case_code per tutte le attività pertinenti. project_code e case_code sono alternativi e non devono essere valorizzati insieme. Un'azione senza orario ma con un giorno resta una create_task con due_date valorizzata e due_time null.
Non creare vendite o movimenti finanziari. Se la richiesta è ambigua usa respond e chiedi conferma."""},
            {"role": "system", "content": context},
        ]
        messages.extend((history or [])[-12:])
        messages.append({"role": "user", "content": raw_text})
        response = await complete(messages, response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "second_brain_action",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["create_event", "create_events", "create_task", "create_tasks", "respond", "draft_article"]},
                        "text": {"type": ["string", "null"]},
                        "title": {"type": ["string", "null"]},
                        "event_date": {"type": ["string", "null"]},
                        "start_time": {"type": ["string", "null"]},
                        "location": {"type": ["string", "null"]},
                        "event_type": {"type": ["string", "null"]},
                        "events": {
                            "type": ["array", "null"],
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "event_date": {"type": "string"},
                                    "start_time": {"type": ["string", "null"]},
                                    "end_time": {"type": ["string", "null"]},
                                    "location": {"type": ["string", "null"]},
                                    "event_type": {"type": "string"},
                                    "project_code": {"type": ["string", "null"]},
                                    "case_code": {"type": ["string", "null"]},
                                },
                                "required": ["title", "event_date", "start_time", "end_time", "location", "event_type", "project_code", "case_code"],
                                "additionalProperties": False,
                            },
                        },
                        "tasks": {
                            "type": ["array", "null"],
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "due_date": {"type": ["string", "null"]},
                                    "due_time": {"type": ["string", "null"]},
                                    "priority": {"type": ["integer", "null"]},
                                    "project_code": {"type": ["string", "null"]},
                                    "case_code": {"type": ["string", "null"]},
                                },
                                "required": ["title", "due_date", "due_time", "priority", "project_code", "case_code"],
                                "additionalProperties": False,
                            },
                        },
                        "due_date": {"type": ["string", "null"]},
                        "due_time": {"type": ["string", "null"]},
                        "priority": {"type": ["integer", "null"]},
                        "project_code": {"type": ["string", "null"]},
                        "case_code": {"type": ["string", "null"]},
                        "subtitle": {"type": ["string", "null"]},
                        "content_markdown": {"type": ["string", "null"]},
                        "author_code": {"type": ["string", "null"]},
                    },
                    "required": ["action", "text", "title", "event_date", "start_time", "location", "event_type", "events", "tasks", "due_date", "due_time", "priority", "project_code", "case_code", "subtitle", "content_markdown", "author_code"],
                    "additionalProperties": False,
                },
            },
        })
        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE)
        payload = json.loads(cleaned)
        action = payload.get("action")
        def linked_ids(project_code: str | None, case_code: str | None) -> tuple:
            if project_code and case_code:
                raise ValueError("Progetto e pratica non possono essere assegnati insieme")
            if project_code:
                project_id = repo.project_id_by_code(project_code)
                if project_id is not None:
                    return project_id, None
                case_id = repo.case_id_by_code(project_code)
                if case_id is not None:
                    return None, case_id
                raise ValueError(f"Progetto o pratica sconosciuti: {project_code}")
            if case_code:
                case_id = repo.case_id_by_code(case_code)
                if case_id is not None:
                    return None, case_id
                project_id = repo.project_id_by_code(case_code)
                if project_id is not None:
                    return project_id, None
                raise ValueError(f"Pratica o progetto sconosciuti: {case_code}")
            return None, None
        if action == "create_event":
            project_id, case_id = linked_ids(payload.get("project_code"), payload.get("case_code"))
            event_date = date.fromisoformat(payload["event_date"])
            start_time = time.fromisoformat(payload["start_time"]) if payload.get("start_time") else None
            item = repo.create_event({
                "title": payload["title"], "event_date": event_date,
                "start_time": start_time, "end_time": None, "location": payload.get("location"),
                "event_type": payload.get("event_type", "personal"),
                "project_id": project_id, "case_id": case_id,
                "author_profile_id": None, "book_id": None,
            })
            return {"mode": "llm", "kind": "event_created", "data": item,
                    "message": f"Evento creato: {item['title']}"}
        if action == "create_events":
            source_events = payload.get("events") or []
            if not source_events:
                raise ValueError("Elenco eventi vuoto")
            pending = []
            for event_data in source_events:
                project_id, case_id = linked_ids(event_data.get("project_code"), event_data.get("case_code"))
                pending.append({
                    "title": event_data["title"],
                    "event_date": date.fromisoformat(event_data["event_date"]),
                    "start_time": time.fromisoformat(event_data["start_time"]) if event_data.get("start_time") else None,
                    "end_time": time.fromisoformat(event_data["end_time"]) if event_data.get("end_time") else None,
                    "location": event_data.get("location"),
                    "event_type": event_data.get("event_type") or "personal",
                    "project_id": project_id,
                    "case_id": case_id,
                    "author_profile_id": None,
                    "book_id": None,
                })
            created = repo.create_events(pending)
            return {"mode": "llm", "kind": "events_created", "data": {"items": created},
                    "message": f"Creati {len(created)} eventi a calendario."}
        if action == "create_task":
            project_id, case_id = linked_ids(payload.get("project_code"), payload.get("case_code"))
            due_date = date.fromisoformat(payload["due_date"]) if payload.get("due_date") else None
            due_time = time.fromisoformat(payload["due_time"]) if payload.get("due_time") else None
            item = repo.create_task({
                "title": payload["title"], "due_date": due_date,
                "due_time": due_time, "priority": payload.get("priority", 3),
                "project_id": project_id, "case_id": case_id, "author_profile_id": None, "book_id": None,
            })
            return {"mode": "llm", "kind": "task_created", "data": item,
                    "message": f"Attività creata: {item['title']}"}
        if action == "create_tasks":
            source_tasks = payload.get("tasks") or []
            if not source_tasks:
                raise ValueError("Elenco attività vuoto")
            pending = []
            for task_data in source_tasks:
                project_id, case_id = linked_ids(task_data.get("project_code"), task_data.get("case_code"))
                pending.append({
                    "title": task_data["title"],
                    "due_date": date.fromisoformat(task_data["due_date"]) if task_data.get("due_date") else None,
                    "due_time": time.fromisoformat(task_data["due_time"]) if task_data.get("due_time") else None,
                    "priority": task_data.get("priority") or 3,
                    "project_id": project_id,
                    "case_id": case_id,
                    "author_profile_id": None,
                    "book_id": None,
                })
            created = repo.create_tasks(pending)
            return {"mode": "llm", "kind": "tasks_created", "data": {"items": created},
                    "message": f"Create {len(created)} attività a calendario."}
        if action == "draft_article":
            data = {key: payload.get(key) for key in ("title", "subtitle", "content_markdown", "author_code")}
            if not data["title"] or not data["content_markdown"]:
                raise ValueError("Articolo incompleto")
            return {"mode": "llm", "kind": "article", "data": data, "message": "Bozza articolo generata."}
        return {"mode": "llm", "kind": "text", "data": {"text": payload.get("text", response)},
                "message": payload.get("text", response)}
    except json.JSONDecodeError:
        return {"mode": "llm", "kind": "text", "data": {"text": response}, "message": response}
    except (KeyError, TypeError, ValueError) as exc:
        item = repo.add_inbox(raw_text, "assistant")
        return {"mode": "queued", "kind": "inbox", "data": item,
                "message": f"Risposta LLM non valida ({exc.__class__.__name__}). Richiesta conservata nell'inbox."}
    except LlmUnavailable as exc:
        item = repo.add_inbox(raw_text, "assistant")
        return {"mode": "queued", "kind": "inbox", "data": item, "message": str(exc)}
