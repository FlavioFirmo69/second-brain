import json
import re
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import text
from sqlalchemy.orm import Session

from .config import get_settings
from .calendar_rules import apply_calendar_rules


def rows(result) -> list[dict[str, Any]]:
    return [dict(item) for item in result.mappings().all()]


class Repository:
    def __init__(self, session: Session):
        self.session = session
        self.settings = get_settings()

    def user_id(self) -> UUID:
        value = self.session.execute(
            text("SELECT id FROM dbo.sb2_users WHERE email=:email AND is_active=1"),
            {"email": self.settings.default_user_email},
        ).scalar_one_or_none()
        if value is None:
            raise RuntimeError("Utente predefinito non trovato. Eseguire lo script di seed.")
        return value

    def today(self) -> date:
        return datetime.now(ZoneInfo(self.settings.app_timezone)).date()

    def apply_calendar_rules(self) -> None:
        apply_calendar_rules(
            self.session,
            self.user_id(),
            datetime.now(ZoneInfo(self.settings.app_timezone)),
        )

    def dashboard(self, target_date: date | None = None) -> dict[str, Any]:
        self.apply_calendar_rules()
        uid = self.user_id()
        day = target_date or self.today()
        tasks = rows(self.session.execute(text("""
            SELECT t.id,t.title,t.status,t.priority,t.due_date,t.due_time,
                   p.title AS project_title,c.title AS case_title,a.display_name AS author_name,b.title AS book_title
            FROM dbo.sb2_tasks t
            LEFT JOIN dbo.sb2_projects p ON p.id=t.project_id
            LEFT JOIN dbo.sb2_cases c ON c.id=t.case_id
            LEFT JOIN dbo.sb2_author_profiles a ON a.id=t.author_profile_id
            LEFT JOIN dbo.sb2_books b ON b.id=t.book_id
            WHERE t.user_id=:uid AND t.status NOT IN (N'completed',N'cancelled')
              AND (t.due_date=:day OR t.due_date IS NULL)
            ORDER BY CASE WHEN t.due_date IS NULL THEN 1 ELSE 0 END,t.due_time,t.priority
        """), {"uid": uid, "day": day}))
        events = rows(self.session.execute(text("""
            SELECT id,title,event_date,start_time,end_time,location,event_type,status
            FROM dbo.sb2_events
            WHERE user_id=:uid AND status NOT IN (N'completed',N'cancelled') AND event_date=:day
            ORDER BY start_time,title
        """), {"uid": uid, "day": day}))
        return {"date": day, "tasks": tasks, "events": events}

    def week(self) -> dict[str, Any]:
        self.apply_calendar_rules()
        uid = self.user_id()
        start = self.today()
        end = start + timedelta(days=6-start.weekday())
        tasks = rows(self.session.execute(text("""
            SELECT id,title,status,priority,due_date,due_time FROM dbo.sb2_tasks
            WHERE user_id=:uid AND status NOT IN (N'completed',N'cancelled')
              AND (due_date BETWEEN :start AND :end OR due_date IS NULL)
            ORDER BY due_date,due_time,priority
        """), {"uid": uid, "start": start, "end": end}))
        events = rows(self.session.execute(text("""
            SELECT id,title,event_date,start_time,location,event_type,status FROM dbo.sb2_events
            WHERE user_id=:uid AND status NOT IN (N'completed',N'cancelled')
              AND event_date BETWEEN :start AND :end
            ORDER BY event_date,start_time
        """), {"uid": uid, "start": start, "end": end}))
        return {"start": start, "end": end, "tasks": tasks, "events": events}

    def list_tasks(self) -> list[dict[str, Any]]:
        self.apply_calendar_rules()
        return rows(self.session.execute(text("""
            SELECT id,title,status,priority,due_date,due_time,completed_at FROM dbo.sb2_tasks
            WHERE user_id=:uid AND status NOT IN (N'completed',N'cancelled')
            ORDER BY CASE WHEN due_date IS NULL THEN 1 ELSE 0 END,due_date,due_time,priority
        """), {"uid": self.user_id()}))

    def create_task(self, data: dict[str, Any]) -> dict[str, Any]:
        uid = self.user_id()
        task_id = self.session.execute(text("""
            INSERT dbo.sb2_tasks(user_id,project_id,case_id,author_profile_id,book_id,title,status,priority,due_date,due_time)
            OUTPUT inserted.id
            VALUES(:uid,:project_id,:case_id,:author_profile_id,:book_id,:title,
                   CASE WHEN :due_date IS NULL THEN N'open' ELSE N'planned' END,:priority,:due_date,:due_time)
        """), {"uid": uid, **data}).scalar_one()
        self.log(uid, "task", task_id, "create", None, data)
        self.session.commit()
        return {"id": task_id, **data}

    def complete_task(self, task_id: UUID) -> None:
        uid = self.user_id()
        before = self.session.execute(text("SELECT * FROM dbo.sb2_tasks WHERE id=:id AND user_id=:uid"), {"id": task_id, "uid": uid}).mappings().one_or_none()
        if before is None:
            raise KeyError("Attività non trovata")
        self.session.execute(text("""
            UPDATE dbo.sb2_tasks SET status=N'completed',completed_at=SYSUTCDATETIME(),updated_at=SYSUTCDATETIME()
            WHERE id=:id AND user_id=:uid
        """), {"id": task_id, "uid": uid})
        self.log(uid, "task", task_id, "complete", dict(before), {"status": "completed"})
        self.session.commit()

    def list_events(self, start: date, end: date) -> list[dict[str, Any]]:
        self.apply_calendar_rules()
        return rows(self.session.execute(text("""
            SELECT id,title,event_date,start_time,end_time,location,status,event_type
            FROM dbo.sb2_events
            WHERE user_id=:uid AND status NOT IN (N'completed',N'cancelled')
              AND event_date BETWEEN :start AND :end
            ORDER BY event_date,start_time,title
        """), {"uid": self.user_id(), "start": start, "end": end}))

    def create_event(self, data: dict[str, Any]) -> dict[str, Any]:
        uid = self.user_id()
        event_id = self.session.execute(text("""
            INSERT dbo.sb2_events(user_id,author_profile_id,book_id,title,event_date,start_time,end_time,location,event_type)
            OUTPUT inserted.id
            VALUES(:uid,:author_profile_id,:book_id,:title,:event_date,:start_time,:end_time,:location,:event_type)
        """), {"uid": uid, **data}).scalar_one()
        self.log(uid, "event", event_id, "create", None, data)
        self.session.commit()
        return {"id": event_id, **data}

    def create_events(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        uid = self.user_id()
        created: list[dict[str, Any]] = []
        for data in items:
            event_id = self.session.execute(text("""
                INSERT dbo.sb2_events(user_id,author_profile_id,book_id,title,event_date,start_time,end_time,location,event_type)
                OUTPUT inserted.id
                VALUES(:uid,:author_profile_id,:book_id,:title,:event_date,:start_time,:end_time,:location,:event_type)
            """), {"uid": uid, **data}).scalar_one()
            self.log(uid, "event", event_id, "create", None, data)
            created.append({"id": event_id, **data})
        self.session.commit()
        return created

    def update_event(self, event_id: UUID, data: dict[str, Any]) -> dict[str, Any]:
        uid = self.user_id()
        before = self.session.execute(
            text("SELECT * FROM dbo.sb2_events WHERE id=:id AND user_id=:uid"),
            {"id": event_id, "uid": uid},
        ).mappings().one_or_none()
        if before is None:
            raise KeyError("Evento non trovato")
        self.session.execute(text("""
            UPDATE dbo.sb2_events SET title=:title,event_date=:event_date,start_time=:start_time,end_time=:end_time,
              location=:location,event_type=:event_type,author_profile_id=:author_profile_id,
              book_id=:book_id,updated_at=SYSUTCDATETIME()
            WHERE id=:id AND user_id=:uid
        """), {"id": event_id, "uid": uid, **data})
        self.log(uid, "event", event_id, "update", dict(before), data)
        self.session.commit()
        return {"id": event_id, **data, "status": before["status"]}

    def complete_event(self, event_id: UUID) -> None:
        self._set_event_status(event_id, "completed", "complete")

    def delete_event(self, event_id: UUID) -> None:
        self._set_event_status(event_id, "cancelled", "delete")

    def _set_event_status(self, event_id: UUID, next_status: str, action: str) -> None:
        uid = self.user_id()
        before = self.session.execute(
            text("SELECT * FROM dbo.sb2_events WHERE id=:id AND user_id=:uid"),
            {"id": event_id, "uid": uid},
        ).mappings().one_or_none()
        if before is None:
            raise KeyError("Evento non trovato")
        self.session.execute(text("""
            UPDATE dbo.sb2_events SET status=:status,updated_at=SYSUTCDATETIME()
            WHERE id=:id AND user_id=:uid
        """), {"id": event_id, "uid": uid, "status": next_status})
        self.log(uid, "event", event_id, action, dict(before), {"status": next_status})
        self.session.commit()

    def profiles(self) -> list[dict[str, Any]]:
        return rows(self.session.execute(text("""
            SELECT id,code,display_name,is_pseudonym,positioning,voice_markdown,privacy_markdown,updated_at
            FROM dbo.sb2_author_profiles WHERE user_id=:uid AND is_active=1 ORDER BY display_name
        """), {"uid": self.user_id()}))

    def update_profile(self, code: str, data: dict[str, Any]) -> dict[str, Any]:
        uid = self.user_id()
        profile = self.session.execute(text("SELECT * FROM dbo.sb2_author_profiles WHERE user_id=:uid AND code=:code"), {"uid": uid, "code": code.upper()}).mappings().one_or_none()
        if profile is None:
            raise KeyError("Profilo non trovato")
        profile_id = profile["id"]
        next_version = self.session.execute(text("SELECT COALESCE(MAX(version_number),0)+1 FROM dbo.sb2_agent_prompt_versions WHERE author_profile_id=:id"), {"id": profile_id}).scalar_one()
        self.session.execute(text("UPDATE dbo.sb2_agent_prompt_versions SET is_active=0 WHERE author_profile_id=:id"), {"id": profile_id})
        content = f"# {profile['display_name']}\n\n## Posizionamento\n{data['positioning']}\n\n## Voce\n{data['voice_markdown']}\n\n## Privacy\n{data['privacy_markdown']}"
        self.session.execute(text("""
            INSERT dbo.sb2_agent_prompt_versions(author_profile_id,version_number,content_markdown,change_reason,is_active)
            VALUES(:id,:version,:content,:reason,1)
        """), {"id": profile_id, "version": next_version, "content": content, "reason": data["change_reason"]})
        self.session.execute(text("""
            UPDATE dbo.sb2_author_profiles SET positioning=:positioning,voice_markdown=:voice_markdown,
              privacy_markdown=:privacy_markdown,updated_at=SYSUTCDATETIME() WHERE id=:id
        """), {"id": profile_id, **{k: data[k] for k in ("positioning", "voice_markdown", "privacy_markdown")}})
        self.log(uid, "author_profile", profile_id, "new_prompt_version", dict(profile), {"version": next_version})
        self.session.commit()
        return {"code": code.upper(), "version_number": next_version}

    def strategies(self) -> list[dict[str, Any]]:
        return rows(self.session.execute(text("""
            SELECT s.id,s.code,s.title,s.content_markdown,s.status,s.version_number,
                   a.display_name AS author_name,b.title AS book_title
            FROM dbo.sb2_strategies s
            LEFT JOIN dbo.sb2_author_profiles a ON a.id=s.author_profile_id
            LEFT JOIN dbo.sb2_books b ON b.id=s.book_id
            WHERE s.user_id=:uid AND s.status=N'active' ORDER BY s.title
        """), {"uid": self.user_id()}))

    def projects(self) -> list[dict[str, Any]]:
        items = rows(self.session.execute(text("""
            SELECT p.id,p.code,p.title,p.status,p.objective,p.notes_markdown,
                   a.display_name AS author_name,b.title AS book_title
            FROM dbo.sb2_projects p
            LEFT JOIN dbo.sb2_author_profiles a ON a.id=p.author_profile_id
            LEFT JOIN dbo.sb2_books b ON b.id=p.book_id
            WHERE p.user_id=:uid ORDER BY p.status,p.title
        """), {"uid": self.user_id()}))
        for item in items:
            item["tasks"] = rows(self.session.execute(text("""
                SELECT id,title,status,priority,due_date,due_time FROM dbo.sb2_tasks
                WHERE user_id=:uid AND project_id=:project_id AND status NOT IN (N'completed',N'cancelled')
                ORDER BY CASE WHEN due_date IS NULL THEN 1 ELSE 0 END,due_date,due_time,priority
            """), {"uid": self.user_id(), "project_id": item["id"]}))
        return items

    def project_id_by_code(self, code: str | None) -> UUID | None:
        if not code:
            return None
        return self.session.execute(text("""
            SELECT id FROM dbo.sb2_projects WHERE user_id=:uid AND UPPER(code)=UPPER(:code)
        """), {"uid": self.user_id(), "code": code.strip()}).scalar_one_or_none()

    def cases(self) -> list[dict[str, Any]]:
        return rows(self.session.execute(text("SELECT id,code,title,status,context_markdown FROM dbo.sb2_cases WHERE user_id=:uid ORDER BY title"), {"uid": self.user_id()}))

    def add_sale(self, data: dict[str, Any]) -> dict[str, Any]:
        uid = self.user_id()
        book = self.session.execute(text("SELECT id,title FROM dbo.sb2_books WHERE code=:code"), {"code": data["book_code"].upper()}).mappings().one_or_none()
        if book is None:
            raise KeyError("Libro non trovato")
        sale_id = self.session.execute(text("""
            INSERT dbo.sb2_sales(user_id,book_id,sale_date,quantity,channel,notes) OUTPUT inserted.id
            VALUES(:uid,:book_id,:sale_date,:quantity,:channel,:notes)
        """), {"uid": uid, "book_id": book["id"], **{k: data.get(k) for k in ("sale_date", "quantity", "channel", "notes")}}).scalar_one()
        self.log(uid, "sale", sale_id, "create", None, data)
        self.session.commit()
        return self.sales_progress(data["book_code"])

    def sales_progress(self, book_code: str | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {"uid": self.user_id()}
        condition = ""
        if book_code:
            condition = " AND b.code=:code"
            params["code"] = book_code.upper()
        items = rows(self.session.execute(text(f"""
            SELECT b.code,b.title,COALESCE(SUM(s.quantity),0) AS sold,
                   t.target_value,t.warning_value,t.target_date
            FROM dbo.sb2_books b
            LEFT JOIN dbo.sb2_sales s ON s.book_id=b.id
            OUTER APPLY (SELECT TOP 1 target_value,warning_value,target_date FROM dbo.sb2_targets x
                         WHERE x.book_id=b.id AND x.metric_code=N'copies_sold' ORDER BY target_date) t
            WHERE b.author_profile_id IN (SELECT id FROM dbo.sb2_author_profiles WHERE user_id=:uid){condition}
            GROUP BY b.code,b.title,t.target_value,t.warning_value,t.target_date
            ORDER BY b.title
        """), params))
        for item in items:
            target = item.get("target_value")
            sold = Decimal(item["sold"])
            item["remaining"] = max(Decimal(0), Decimal(target) - sold) if target is not None else None
            item["status"] = "target_reached" if target is not None and sold >= Decimal(target) else "in_progress"
        return {"items": items}

    def finance(self) -> dict[str, Any]:
        uid = self.user_id()
        account = self.session.execute(text("SELECT TOP 1 id,code,display_name FROM dbo.sb2_accounts WHERE user_id=:uid AND code=N'ING_CURRENT'"), {"uid": uid}).mappings().one()
        balance = self.session.execute(text("""
            SELECT TOP 1 balance,balance_date,reconciliation_amount FROM dbo.sb2_balance_checks
            WHERE account_id=:account ORDER BY balance_date DESC,created_at DESC
        """), {"account": account["id"]}).mappings().one_or_none()
        planned = rows(self.session.execute(text("""
            SELECT id,transaction_date,description,amount,status FROM dbo.sb2_transactions
            WHERE account_id=:account AND status=N'planned' AND transaction_date>=:today
            ORDER BY transaction_date
        """), {"account": account["id"], "today": self.today()}))
        running = Decimal(balance["balance"]) if balance else Decimal(0)
        for movement in planned:
            running += Decimal(movement["amount"])
            movement["projected_balance"] = running
        return {"account": dict(account), "balance": dict(balance) if balance else None, "planned": planned}

    def set_balance(self, data: dict[str, Any]) -> dict[str, Any]:
        uid = self.user_id()
        account = self.session.execute(text("SELECT id FROM dbo.sb2_accounts WHERE user_id=:uid AND code=:code"), {"uid": uid, "code": data["account_code"]}).scalar_one_or_none()
        if account is None:
            raise KeyError("Conto non trovato")
        previous = self.session.execute(text("SELECT TOP 1 balance FROM dbo.sb2_balance_checks WHERE account_id=:id ORDER BY balance_date DESC,created_at DESC"), {"id": account}).scalar_one_or_none()
        reconciliation = data["balance"] - Decimal(previous) if previous is not None else None
        check_id = self.session.execute(text("""
            INSERT dbo.sb2_balance_checks(user_id,account_id,balance_date,balance,previous_balance,reconciliation_amount,notes)
            OUTPUT inserted.id VALUES(:uid,:account,:balance_date,:balance,:previous,:reconciliation,:notes)
        """), {"uid": uid, "account": account, "previous": previous, "reconciliation": reconciliation, **data}).scalar_one()
        self.log(uid, "balance_check", check_id, "create", None, {**data, "reconciliation": reconciliation})
        self.session.commit()
        return {"id": check_id, "reconciliation_amount": reconciliation, **data}

    def inbox(self) -> list[dict[str, Any]]:
        items = rows(self.session.execute(text("SELECT id,source,text,status,created_at,processed_at FROM dbo.sb2_inbox WHERE user_id=:uid AND status<>N'cancelled' ORDER BY created_at DESC"), {"uid": self.user_id()}))
        for item in items:
            item["can_execute"] = self.can_execute_inbox(item["text"]) and item["status"] == "new"
        return items

    def can_execute_inbox(self, value: str) -> bool:
        command = " ".join(value.lower().strip().split())
        deterministic = (
            re.fullmatch(r"(?:todo\s*:|todo|aggiungi todo|da fare\s*:?)\s*.+", command)
            or re.fullmatch(r"(?:stasera|oggi|domani)(?:\s+alle)?\s+\d{1,2}(?::\d{2})?\s+.+", command)
            or re.fullmatch(r"ho venduto\s+\d+\s+copie\s+di\s+.+", command)
        )
        if deterministic:
            return True
        llm_action = re.match(r"^(crea|aggiungi|inserisci|pianifica|programma|segna)\b", command) and any(
            word in command for word in ("evento", "appuntamento", "attività", "todo", "promemoria")
        )
        return bool(llm_action and self.settings.llm_enabled and self.settings.llm_api_key)

    def inbox_item(self, item_id: UUID) -> dict[str, Any]:
        item = self.session.execute(text("SELECT id,source,text,status,created_at FROM dbo.sb2_inbox WHERE id=:id AND user_id=:uid"), {"id": item_id, "uid": self.user_id()}).mappings().one_or_none()
        if item is None:
            raise KeyError("Elemento inbox non trovato")
        return dict(item)

    def complete_inbox(self, item_id: UUID, interpretation: dict[str, Any]) -> None:
        self.session.execute(text("""
            UPDATE dbo.sb2_inbox SET status=N'confirmed',processed_at=SYSUTCDATETIME(),interpretation_json=:result
            WHERE id=:id AND user_id=:uid
        """), {"id": item_id, "uid": self.user_id(), "result": json.dumps(interpretation, ensure_ascii=False, default=str)})
        self.session.commit()

    def delete_inbox(self, item_id: UUID) -> None:
        result = self.session.execute(text("DELETE dbo.sb2_inbox WHERE id=:id AND user_id=:uid"), {"id": item_id, "uid": self.user_id()})
        if result.rowcount == 0:
            raise KeyError("Elemento inbox non trovato")
        self.session.commit()

    def add_inbox(self, text_value: str, source: str) -> dict[str, Any]:
        uid = self.user_id()
        item_id = self.session.execute(text("INSERT dbo.sb2_inbox(user_id,source,text) OUTPUT inserted.id VALUES(:uid,:source,:text)"), {"uid": uid, "source": source, "text": text_value}).scalar_one()
        self.log(uid, "inbox", item_id, "create", None, {"source": source, "text": text_value})
        self.session.commit()
        return {"id": item_id, "source": source, "text": text_value, "status": "new"}

    def commands(self) -> dict[str, list[str]]:
        return {
            "agenda": ["oggi", "settimana", "calendario", "todo"],
            "editoria": ["strategia Flavio", "strategia Cesare", "stato Peter", "stato Rubicone", "ho venduto N copie di LIBRO"],
            "finanze": ["saldo", "saldo N", "movimenti"],
            "sistema": ["inbox", "nota TESTO", "comandi"],
        }

    def list_conversations(self) -> list[dict[str, Any]]:
        return rows(self.session.execute(text("""
            SELECT id,title,status,created_at,updated_at FROM dbo.sb2_conversations
            WHERE user_id=:uid AND status=N'active' ORDER BY updated_at DESC
        """), {"uid": self.user_id()}))

    def create_conversation(self, title: str = "Nuova conversazione") -> dict[str, Any]:
        uid = self.user_id()
        item = self.session.execute(text("""
            INSERT dbo.sb2_conversations(user_id,title) OUTPUT inserted.id,inserted.title,
              inserted.status,inserted.created_at,inserted.updated_at VALUES(:uid,:title)
        """), {"uid": uid, "title": title.strip()[:250]}).mappings().one()
        self.session.commit()
        return dict(item)

    def conversation_messages(self, conversation_id: UUID) -> list[dict[str, Any]]:
        items = rows(self.session.execute(text("""
            SELECT m.id,m.role,m.content_markdown,m.message_kind,m.metadata_json,m.created_at
            FROM dbo.sb2_messages m JOIN dbo.sb2_conversations c ON c.id=m.conversation_id
            WHERE m.conversation_id=:id AND c.user_id=:uid ORDER BY m.created_at,m.id
        """), {"id": conversation_id, "uid": self.user_id()}))
        for item in items:
            item["metadata"] = json.loads(item.pop("metadata_json")) if item.get("metadata_json") else None
        return items

    def add_conversation_message(self, conversation_id: UUID, role: str, content: str,
                                 kind: str = "text", metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        uid = self.user_id()
        exists = self.session.execute(text("""
            SELECT 1 FROM dbo.sb2_conversations WHERE id=:id AND user_id=:uid AND status=N'active'
        """), {"id": conversation_id, "uid": uid}).scalar_one_or_none()
        if exists is None:
            raise KeyError("Conversazione non trovata")
        item = self.session.execute(text("""
            INSERT dbo.sb2_messages(conversation_id,role,content_markdown,message_kind,metadata_json)
            OUTPUT inserted.id,inserted.role,inserted.content_markdown,inserted.message_kind,inserted.created_at
            VALUES(:id,:role,:content,:kind,:metadata)
        """), {"id": conversation_id, "role": role, "content": content, "kind": kind,
                 "metadata": json.dumps(metadata, ensure_ascii=False, default=str) if metadata else None}).mappings().one()
        count = self.session.execute(text("SELECT COUNT(*) FROM dbo.sb2_messages WHERE conversation_id=:id AND role=N'user'"), {"id": conversation_id}).scalar_one()
        title_sql = ",title=:title" if role == "user" and count == 1 else ""
        params = {"id": conversation_id, "title": content.strip().replace("\n", " ")[:80]}
        self.session.execute(text(f"UPDATE dbo.sb2_conversations SET updated_at=SYSUTCDATETIME(){title_sql} WHERE id=:id"), params)
        self.session.commit()
        result = dict(item)
        result["metadata"] = metadata
        return result

    def log(self, uid: UUID, entity_type: str, entity_id: UUID | None, action: str, before: Any, after: Any) -> None:
        def convert(value: Any) -> str | None:
            return json.dumps(value, ensure_ascii=False, default=str) if value is not None else None
        self.session.execute(text("""
            INSERT dbo.sb2_change_log(user_id,entity_type,entity_id,action,before_json,after_json)
            VALUES(:uid,:entity_type,:entity_id,:action,:before_json,:after_json)
        """), {"uid": uid, "entity_type": entity_type, "entity_id": entity_id, "action": action, "before_json": convert(before), "after_json": convert(after)})
