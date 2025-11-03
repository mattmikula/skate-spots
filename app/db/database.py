"""Database configuration and session management."""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_settings

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


@lru_cache
def _load_settings():
    return get_settings()


def _ensure_async_driver(url: str) -> str:
    """Return an async-compatible database URL for the configured backend."""

    if url.startswith("sqlite+aiosqlite://") or url.startswith("postgresql+asyncpg://"):
        return url
    if url.startswith("sqlite://"):
        return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


settings = _load_settings()

_engine_kwargs: dict[str, object] = {"future": True}
if settings.database_url.startswith("sqlite"):
    _engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(settings.database_url, **_engine_kwargs)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)

async_engine: AsyncEngine = create_async_engine(
    _ensure_async_driver(settings.database_url),
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


def get_engine():
    """Return the configured SQLAlchemy engine."""

    return engine


def get_db():
    """Get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session for FastAPI dependencies."""

    async with AsyncSessionLocal() as session:
        yield session
