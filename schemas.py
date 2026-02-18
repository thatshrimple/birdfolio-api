from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


# ── Users ─────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    telegram_id: int
    region: str


class User(BaseModel):
    telegram_id: int
    region: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Sightings ─────────────────────────────────────────────────────────────────

class SightingCreate(BaseModel):
    common_name: str
    scientific_name: str
    rarity: str
    region: str
    date_spotted: date
    notes: Optional[str] = ""
    card_png_url: Optional[str] = ""


class SightingOut(BaseModel):
    id: int
    telegram_id: int
    common_name: str
    scientific_name: str
    rarity: str
    region: str
    date_spotted: date
    is_lifer: bool
    notes: str
    card_png_url: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Checklist ─────────────────────────────────────────────────────────────────

class ChecklistItem(BaseModel):
    id: int
    telegram_id: int
    region: str
    species: str
    slug: str
    rarity_tier: str
    found: bool
    date_found: Optional[date]

    model_config = {"from_attributes": True}


class ChecklistItemCreate(BaseModel):
    region: str
    species: str
    slug: str
    rarity_tier: str


# ── Stats ─────────────────────────────────────────────────────────────────────

class RarestBird(BaseModel):
    common_name: str
    rarity: str
    date_spotted: date

class MostRecent(BaseModel):
    common_name: str
    date_spotted: date

class Stats(BaseModel):
    total_sightings: int
    total_species: int
    rarest_bird: Optional[RarestBird]
    most_recent: Optional[MostRecent]
