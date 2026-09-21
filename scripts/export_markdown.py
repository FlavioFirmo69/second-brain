"""Esporta viste leggibili dal database. Avviare dalla radice del progetto."""
from datetime import date, timedelta
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from sqlalchemy.orm import Session  # noqa: E402
from app.database import get_engine  # noqa: E402
from app.repository import Repository  # noqa: E402


def main() -> None:
    target = ROOT / "exports" / date.today().isoformat()
    target.mkdir(parents=True, exist_ok=True)
    with Session(get_engine()) as session:
        repo = Repository(session)
        today = repo.dashboard()
        week = repo.week()
        finance = repo.finance()
        strategies = repo.strategies()

    lines = [f"# Oggi — {today['date']}", "", "## Eventi"]
    lines += [f"- {str(item.get('start_time') or '')[:5]} {item['title']}" for item in today["events"]] or ["- Nessuno"]
    lines += ["", "## Attività"]
    lines += [f"- {item['title']}" for item in today["tasks"]] or ["- Nessuna"]
    (target / "oggi.md").write_text("\n".join(lines), encoding="utf-8")

    calendar = [f"# Settimana — {week['start']} / {week['end']}", ""]
    calendar += [f"- {item['event_date']} {str(item.get('start_time') or '')[:5]} {item['title']}" for item in week["events"]]
    calendar += [f"- {item.get('due_date') or 'TODO'} {item['title']}" for item in week["tasks"]]
    (target / "settimana.md").write_text("\n".join(calendar), encoding="utf-8")

    money = ["# Finanze", "", f"Saldo: {finance.get('balance', {}).get('balance', '—')}", "", "## Previsti"]
    money += [f"- {item['transaction_date']} {item['description']}: {item['amount']}" for item in finance["planned"]]
    (target / "finanze.md").write_text("\n".join(money), encoding="utf-8")

    for item in strategies:
        (target / f"strategia-{item['code'].lower()}.md").write_text(f"# {item['title']}\n\n{item['content_markdown']}\n", encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()

