"""Trasferisce le tabelle sb2_* da SQL Server a Supabase/PostgreSQL.

Eseguire dalla radice del progetto dopo aver configurato backend/.env.
Il trasferimento conserva gli UUID e usa ON CONFLICT DO NOTHING, quindi una
seconda esecuzione non duplica i record già presenti.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any
from uuid import UUID
from dotenv import dotenv_values
from sqlalchemy import create_engine, text


ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / "backend" / ".env"

TABLES = [
    "sb2_users",
    "sb2_author_profiles",
    "sb2_agent_prompt_versions",
    "sb2_channels",
    "sb2_books",
    "sb2_strategies",
    "sb2_projects",
    "sb2_cases",
    "sb2_tasks",
    "sb2_events",
    "sb2_sales",
    "sb2_targets",
    "sb2_accounts",
    "sb2_transactions",
    "sb2_balance_checks",
    "sb2_inbox",
    "sb2_change_log",
    "sb2_conversations",
    "sb2_messages",
]

BOOLEAN_COLUMNS = {
    "sb2_users": {"is_active"},
    "sb2_author_profiles": {"is_pseudonym", "is_active"},
    "sb2_agent_prompt_versions": {"is_active"},
    "sb2_channels": {"is_active"},
    "sb2_accounts": {"include_in_projection", "is_active"},
    "sb2_transactions": {"is_recurring"},
}

UUID_COLUMNS = {
    "id", "user_id", "author_profile_id", "book_id", "project_id", "case_id",
    "account_id", "conversation_id", "entity_id",
}


def setting(values: dict[str, str | None], name: str, legacy: str | None = None) -> str:
    value = os.getenv(name) or values.get(name)
    if not value and legacy:
        value = os.getenv(legacy) or values.get(legacy)
    return str(value or "").strip()


def postgres_url(raw: str) -> str:
    if raw.startswith("postgresql://"):
        return raw.replace("postgresql://", "postgresql+psycopg://", 1)
    if raw.startswith("postgres://"):
        return raw.replace("postgres://", "postgresql+psycopg://", 1)
    return raw


def source_connection(values: dict[str, str | None]) -> Any:
    try:
        import pyodbc
    except (ImportError, OSError) as exc:
        raise RuntimeError(
            "pyodbc o il driver ODBC non sono disponibili. "
            "Installare backend/requirements-migration.txt ed eseguire lo script su Windows."
        ) from exc
    required = {
        "server": setting(values, "SOURCE_DB_SERVER", "DB_SERVER"),
        "database": setting(values, "SOURCE_DB_NAME", "DB_NAME"),
        "user": setting(values, "SOURCE_DB_USER", "DB_USER"),
        "password": setting(values, "SOURCE_DB_PASSWORD", "DB_PASSWORD"),
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise RuntimeError("Credenziali SQL Server mancanti: " + ", ".join(missing))
    driver = setting(values, "SOURCE_DB_DRIVER", "DB_DRIVER") or "ODBC Driver 17 for SQL Server"
    encrypt = setting(values, "SOURCE_DB_ENCRYPT", "DB_ENCRYPT") or "yes"
    trust = setting(values, "SOURCE_DB_TRUST_SERVER_CERTIFICATE", "DB_TRUST_SERVER_CERTIFICATE") or "no"
    connection_string = (
        f"DRIVER={{{driver}}};SERVER={required['server']};DATABASE={required['database']};"
        f"UID={required['user']};PWD={required['password']};Encrypt={encrypt};"
        f"TrustServerCertificate={trust};"
    )
    return pyodbc.connect(connection_string)


def convert_value(table: str, column: str, value):
    if value is None:
        return None
    if column in BOOLEAN_COLUMNS.get(table, set()):
        return bool(value)
    # sb2_change_log.id e' BIGINT; negli altri record la colonna id e' UUID.
    is_uuid = column in UUID_COLUMNS and not (table == "sb2_change_log" and column == "id")
    if is_uuid:
        return UUID(str(value))
    return value


def read_table(cursor: Any, table: str) -> tuple[list[str], list[dict]]:
    cursor.execute(f"SELECT * FROM dbo.{table}")
    columns = [item[0] for item in cursor.description]
    result = []
    for source_row in cursor.fetchall():
        result.append({
            column: convert_value(table, column, value)
            for column, value in zip(columns, source_row, strict=True)
        })
    return columns, result


def destination_count(connection, table: str) -> int:
    return int(connection.execute(text(f"SELECT COUNT(*) FROM public.{table}")).scalar_one())


def main() -> int:
    parser = argparse.ArgumentParser(description="Migra Second Brain da SQL Server a Supabase")
    parser.add_argument("--dry-run", action="store_true", help="Mostra i conteggi senza scrivere")
    args = parser.parse_args()

    values = dict(dotenv_values(ENV_FILE))
    target_url = setting(values, "DATABASE_URL")
    if not target_url:
        raise RuntimeError("DATABASE_URL non presente in backend/.env")

    target_engine = create_engine(
        postgres_url(target_url),
        pool_pre_ping=True,
        connect_args={"prepare_threshold": None},
    )

    print("Connessione a SQL Server e Supabase...")
    with source_connection(values) as source, target_engine.begin() as target:
        cursor = source.cursor()
        for table in TABLES:
            columns, records = read_table(cursor, table)
            before = destination_count(target, table)
            if records and not args.dry_run:
                quoted_columns = ", ".join(f'"{column}"' for column in columns)
                placeholders = ", ".join(f":{column}" for column in columns)
                statement = text(
                    f"INSERT INTO public.{table} ({quoted_columns}) "
                    f"VALUES ({placeholders}) ON CONFLICT DO NOTHING"
                )
                for start in range(0, len(records), 500):
                    target.execute(statement, records[start:start + 500])
            after = before if args.dry_run else destination_count(target, table)
            print(f"{table}: sorgente={len(records)}, prima={before}, dopo={after}")

        if not args.dry_run:
            target.execute(text("""
                SELECT setval(
                    pg_get_serial_sequence('public.sb2_change_log', 'id'),
                    COALESCE(MAX(id), 1),
                    MAX(id) IS NOT NULL
                )
                FROM public.sb2_change_log
            """))

    print("Controllo completato." if args.dry_run else "Migrazione completata.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERRORE: {exc}", file=sys.stderr)
        raise SystemExit(1)
