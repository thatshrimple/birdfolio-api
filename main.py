from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import models, schemas, crud
from database import engine, get_db
from contextlib import asynccontextmanager
import os


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Tables are created on first /health or /setup call — not at boot
    # This avoids Railway internal network not being ready at container startup
    yield


app = FastAPI(title="Birdfolio API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/health")
async def health():
    return {"status": "ok"}


# ── PWA ───────────────────────────────────────────────────────────────────────

def _app_html() -> str:
    path = os.path.join(os.path.dirname(__file__), "frontend", "app.html")
    with open(path, encoding="utf-8") as f:
        return f.read()

@app.get("/", response_class=HTMLResponse)
async def root():
    return HTMLResponse(_app_html())

@app.get("/{telegram_id_str}", response_class=HTMLResponse)
async def pwa_page(telegram_id_str: str):
    # Only serve PWA for numeric IDs; let other routes fall through
    if not telegram_id_str.isdigit():
        raise HTTPException(status_code=404)
    return HTMLResponse(_app_html())


@app.post("/setup")
async def setup():
    """Create all tables. Call once after first deploy."""
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    return {"status": "tables created"}


# ── Users ────────────────────────────────────────────────────────────────────

@app.post("/users", response_model=schemas.User)
async def upsert_user(payload: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    return await crud.upsert_user(db, payload)


@app.get("/users/{telegram_id}", response_model=schemas.User)
async def get_user(telegram_id: int, db: AsyncSession = Depends(get_db)):
    user = await crud.get_user(db, telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ── Sightings ────────────────────────────────────────────────────────────────

@app.post("/users/{telegram_id}/sightings", response_model=schemas.SightingOut)
async def log_sighting(
    telegram_id: int,
    payload: schemas.SightingCreate,
    db: AsyncSession = Depends(get_db)
):
    return await crud.log_sighting(db, telegram_id, payload)


@app.get("/users/{telegram_id}/sightings", response_model=list[schemas.SightingOut])
async def list_sightings(telegram_id: int, db: AsyncSession = Depends(get_db)):
    return await crud.list_sightings(db, telegram_id)


# ── Checklist ────────────────────────────────────────────────────────────────

@app.get("/users/{telegram_id}/checklist", response_model=list[schemas.ChecklistItem])
async def get_checklist(telegram_id: int, db: AsyncSession = Depends(get_db)):
    return await crud.get_checklist(db, telegram_id)


@app.patch("/users/{telegram_id}/checklist/{slug}", response_model=schemas.ChecklistItem)
async def mark_found(
    telegram_id: int,
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    item = await crud.mark_found(db, telegram_id, slug)
    if not item:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    return item


# ── Stats ────────────────────────────────────────────────────────────────────

@app.get("/users/{telegram_id}/stats", response_model=schemas.Stats)
async def get_stats(telegram_id: int, db: AsyncSession = Depends(get_db)):
    return await crud.get_stats(db, telegram_id)
