from sqlalchemy import BigInteger, Boolean, Column, Date, DateTime, Integer, String, ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    telegram_id = Column(BigInteger, primary_key=True, index=True)
    region      = Column(String, nullable=False)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    sightings   = relationship("Sighting", back_populates="user", cascade="all, delete")
    checklist   = relationship("ChecklistItem", back_populates="user", cascade="all, delete")


class Sighting(Base):
    __tablename__ = "sightings"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id     = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False, index=True)
    common_name     = Column(String, nullable=False)
    scientific_name = Column(String, nullable=False)
    rarity          = Column(String, nullable=False)  # common / rare / superRare / bonus
    region          = Column(String, nullable=False)
    date_spotted    = Column(Date, nullable=False)
    is_lifer        = Column(Boolean, default=False)
    notes           = Column(String, default="")
    card_png_url    = Column(String, default="")
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="sightings")


class ChecklistItem(Base):
    __tablename__ = "checklist"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False, index=True)
    region      = Column(String, nullable=False)
    species     = Column(String, nullable=False)
    slug        = Column(String, nullable=False)
    rarity_tier = Column(String, nullable=False)  # common / rare / superRare
    found       = Column(Boolean, default=False)
    date_found  = Column(Date, nullable=True)

    user = relationship("User", back_populates="checklist")
