import logging
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from .api import router
from .calendar_rules import convert_past_project_book_events
from .database import get_engine
from .planning import router as planning_router
from .repository import Repository
from .config import get_settings
from .version import APP_VERSION
from .work import router as work_router

settings = get_settings()
logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(_: FastAPI):
    """All'avvio converte in TODO i vecchi eventi di progetti e libri ancora aperti.
    Un errore (per esempio database non raggiungibile) non impedisce l'avvio."""
    try:
        with Session(get_engine()) as session:
            created = convert_past_project_book_events(
                session,
                Repository(session).user_id(),
                datetime.now(ZoneInfo(settings.app_timezone)),
            )
        logger.info("Avvio: %s eventi passati di progetti/libri convertiti in TODO", created)
    except Exception:
        logger.exception("Avvio: conversione eventi passati di progetti/libri non eseguita")
    yield


app = FastAPI(title=settings.app_name, version=APP_VERSION, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)
app.include_router(work_router)
app.include_router(planning_router)

# In locale il frontend continua a essere servito da Vite sulla porta 5173.
# Durante la build Vercel crea frontend/dist e FastAPI lo pubblica alla radice.
frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
