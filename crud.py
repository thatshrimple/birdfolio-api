from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from datetime import date
import models, schemas


RARITY_RANK = {"superRare": 3, "rare": 2, "common": 1, "bonus": 0}


# ── Users ─────────────────────────────────────────────────────────────────────

async def upsert_user(db: AsyncSession, payload: schemas.UserCreate) -> models.User:
    result = await db.execute(
        select(models.User).where(models.User.telegram_id == payload.telegram_id)
    )
    user = result.scalar_one_or_none()
    if user:
        user.region = payload.region
    else:
        user = models.User(telegram_id=payload.telegram_id, region=payload.region)
        db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_user(db: AsyncSession, telegram_id: int) -> models.User | None:
    result = await db.execute(
        select(models.User).where(models.User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


# ── Sightings ─────────────────────────────────────────────────────────────────

async def log_sighting(
    db: AsyncSession, telegram_id: int, payload: schemas.SightingCreate
) -> models.Sighting:
    # Auto-create user if not exists (uses region from existing or defaults)
    user = await get_user(db, telegram_id)
    if not user:
        user = models.User(telegram_id=telegram_id, region=payload.region)
        db.add(user)
        await db.flush()

    # Determine if lifer
    existing = await db.execute(
        select(models.Sighting).where(
            models.Sighting.telegram_id == telegram_id,
            models.Sighting.common_name == payload.common_name,
        )
    )
    is_lifer = existing.scalar_one_or_none() is None

    sighting = models.Sighting(
        telegram_id=telegram_id,
        common_name=payload.common_name,
        scientific_name=payload.scientific_name,
        rarity=payload.rarity,
        region=payload.region,
        date_spotted=payload.date_spotted,
        is_lifer=is_lifer,
        notes=payload.notes or "",
        card_png_url=payload.card_png_url or "",
    )
    db.add(sighting)
    await db.commit()
    await db.refresh(sighting)
    return sighting


async def list_sightings(db: AsyncSession, telegram_id: int) -> list[models.Sighting]:
    result = await db.execute(
        select(models.Sighting)
        .where(models.Sighting.telegram_id == telegram_id)
        .order_by(models.Sighting.created_at.desc())
    )
    return result.scalars().all()


# ── Checklist ─────────────────────────────────────────────────────────────────

async def get_checklist(db: AsyncSession, telegram_id: int) -> list[models.ChecklistItem]:
    result = await db.execute(
        select(models.ChecklistItem).where(models.ChecklistItem.telegram_id == telegram_id)
    )
    return result.scalars().all()


async def mark_found(
    db: AsyncSession, telegram_id: int, slug: str
) -> models.ChecklistItem | None:
    result = await db.execute(
        select(models.ChecklistItem).where(
            models.ChecklistItem.telegram_id == telegram_id,
            models.ChecklistItem.slug == slug,
        )
    )
    item = result.scalar_one_or_none()
    if item:
        item.found = True
        item.date_found = date.today()
        await db.commit()
        await db.refresh(item)
    return item


async def bulk_create_checklist(
    db: AsyncSession, telegram_id: int, items: list[schemas.ChecklistItemCreate]
):
    """Called during setup to populate the checklist."""
    for item in items:
        db.add(models.ChecklistItem(
            telegram_id=telegram_id,
            region=item.region,
            species=item.species,
            slug=item.slug,
            rarity_tier=item.rarity_tier,
            found=False,
        ))
    await db.commit()


# ── Stats ─────────────────────────────────────────────────────────────────────

async def get_stats(db: AsyncSession, telegram_id: int) -> schemas.Stats:
    # Total sightings
    total_result = await db.execute(
        select(func.count()).where(models.Sighting.telegram_id == telegram_id)
    )
    total_sightings = total_result.scalar() or 0

    # Total unique species (lifers)
    species_result = await db.execute(
        select(func.count()).where(
            models.Sighting.telegram_id == telegram_id,
            models.Sighting.is_lifer == True,
        )
    )
    total_species = species_result.scalar() or 0

    # Most recent lifer
    recent_result = await db.execute(
        select(models.Sighting)
        .where(models.Sighting.telegram_id == telegram_id, models.Sighting.is_lifer == True)
        .order_by(models.Sighting.date_spotted.desc())
        .limit(1)
    )
    recent = recent_result.scalar_one_or_none()

    # Rarest bird (by rarity rank, then most recent)
    lifers_result = await db.execute(
        select(models.Sighting)
        .where(models.Sighting.telegram_id == telegram_id, models.Sighting.is_lifer == True)
    )
    lifers = lifers_result.scalars().all()
    rarest = max(lifers, key=lambda s: RARITY_RANK.get(s.rarity, 0), default=None) if lifers else None

    return schemas.Stats(
        total_sightings=total_sightings,
        total_species=total_species,
        rarest_bird=schemas.RarestBird(
            common_name=rarest.common_name,
            rarity=rarest.rarity,
            date_spotted=rarest.date_spotted,
        ) if rarest else None,
        most_recent=schemas.MostRecent(
            common_name=recent.common_name,
            date_spotted=recent.date_spotted,
        ) if recent else None,
    )
