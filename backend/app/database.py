from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from .config import get_settings

_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        database_url = get_settings().database_url.strip()
        if not database_url:
            raise RuntimeError("DATABASE_URL non configurata")
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
        elif database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
        _engine = create_engine(
            database_url,
            pool_pre_ping=True,
            pool_recycle=300,
            connect_args={"prepare_threshold": None},
            future=True,
        )
    return _engine


def get_session() -> Generator[Session, None, None]:
    with Session(get_engine()) as session:
        yield session
