import asyncio
import logging
from contextlib import suppress
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from .api import router
from .calendar_rules import apply_calendar_rules
from .database import get_engine
from .planning import router as planning_router
from .repository import Repository
from .config import get_settings
from .version import APP_VERSION
from .work import router as work_router
from .strategic import router as strategic_router
from .personal_profile import router as personal_profile_router

settings = get_settings()
logger = logging.getLogger("uvicorn.error")


def run_housekeeping() -> None:
    try:
        with Session(get_engine()) as session:
            apply_calendar_rules(session, Repository(session).user_id(),
                                 datetime.now(ZoneInfo(settings.app_timezone)))
    except Exception:
        logger.exception("Controllo movimenti ed eventi non eseguito; verrà ritentato")


async def housekeeping_loop() -> None:
    while True:
        await asyncio.sleep(60)
        await asyncio.to_thread(run_housekeeping)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Checks the entire backlog at startup, then catches date changes while running.
    await asyncio.to_thread(run_housekeeping)
    task = asyncio.create_task(housekeeping_loop())
    try:
        yield
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


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
app.include_router(strategic_router)
app.include_router(personal_profile_router)

# In locale il frontend continua a essere servito da Vite sulla porta 5173.
# Durante la build Vercel crea frontend/dist e FastAPI lo pubblica alla radice.
frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
