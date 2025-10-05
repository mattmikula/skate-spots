
"""Shared test fixtures and configuration."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base
from app.repositories.skate_spot_repository import SkateSpotRepository
from app.services.skate_spot_service import (
    SkateSpotService,
    get_skate_spot_service,
)
from main import app


@pytest.fixture
def session_factory():
    """Create an in-memory SQLite session factory for tests."""

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    TestSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )
    try:
        yield TestSessionLocal
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def fresh_service(session_factory):
    """Return a service wired to the test session factory."""

    repository = SkateSpotRepository(session_factory=session_factory)
    return SkateSpotService(repository)


@pytest.fixture
def client(session_factory):
    """Create a FastAPI test client with a test database."""

    repository = SkateSpotRepository(session_factory=session_factory)
    service = SkateSpotService(repository)

    app.dependency_overrides[get_skate_spot_service] = lambda: service
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_skate_spot_service, None)
