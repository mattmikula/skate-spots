"""Database configuration and session management."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

BASE_DIR = Path(__file__).resolve().parents[2]
DATABASE_FILE = BASE_DIR / "skate_spots.db"
DATABASE_URL = f"sqlite:///{DATABASE_FILE}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


# Ensure the database file exists early for local development
DATABASE_FILE.touch(exist_ok=True)


def init_db() -> None:
    """Create database tables if they do not yet exist."""

    Base.metadata.create_all(bind=engine)
