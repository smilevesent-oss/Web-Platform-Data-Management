from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .db_init import init_db
from .models import Setting
from .permissions import DEFAULT_SETTINGS
from .routers import admin, analytics, auth, documents, engagement, moderation, taxonomy

PUBLIC_SETTINGS = ("site_name", "site_tagline", "registration_open", "comments_enabled", "default_page_size")


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()  # create tables / view / RBAC baseline if missing
    yield


app = FastAPI(
    title="Enterprise Document & Research Repository API",
    version="1.0.0",
    description="Phase 1: CRUD, authentication and RBAC. Includes the document store and "
    "search/click logging that Phase 2 (inverted index, BM25/TF-IDF) will build on.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (auth, documents, engagement, taxonomy, moderation, admin, analytics):
    app.include_router(r.router, prefix="/api")


@app.get("/api/health", tags=["meta"])
def health():
    return {"status": "ok"}


@app.get("/api/site", tags=["meta"])
def site_settings(db: Session = Depends(get_db)):
    """Public subset of global settings used by the frontend."""
    stored = {s.key: s.value for s in db.scalars(select(Setting).where(Setting.key.in_(PUBLIC_SETTINGS)))}
    return {k: stored.get(k, DEFAULT_SETTINGS[k][0]) for k in PUBLIC_SETTINGS}
