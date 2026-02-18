from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import models, schemas, crud
from database import engine, get_db
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    yield


app = FastAPI(title="Birdfolio API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


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
