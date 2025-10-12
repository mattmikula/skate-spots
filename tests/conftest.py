"""Shared test fixtures and configuration."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.dependencies import get_user_repository
from app.core.security import create_access_token, get_password_hash
from app.db.database import Base, get_db
from app.models.user import UserCreate
from app.repositories.skate_spot_repository import SkateSpotRepository
from app.repositories.user_repository import UserRepository
from app.services.skate_spot_service import (
    SkateSpotService,
    get_skate_spot_service,
)
from app.core.rate_limiter import rate_limiter
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


@pytest.fixture(autouse=True)
def reset_rate_limits():
    """Ensure rate limiter state is cleared between tests."""

    rate_limiter.reset()
    yield
    rate_limiter.reset()


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

    # Override database session
    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    def override_get_user_repository():
        db = session_factory()
        try:
            yield UserRepository(db)
        finally:
            db.close()

    app.dependency_overrides[get_skate_spot_service] = lambda: service
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_user_repository] = override_get_user_repository

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_skate_spot_service, None)
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_user_repository, None)


@pytest.fixture
def test_user(session_factory):
    """Create a test user in the database."""
    db = session_factory()
    try:
        repo = UserRepository(db)
        user_data = UserCreate(
            email="testuser@example.com",
            username="testuser",
            password="password123",
        )
        hashed_password = get_password_hash("password123")
        user = repo.create(user_data, hashed_password)
        db.expunge(user)
        return user
    finally:
        db.close()


@pytest.fixture
def test_admin(session_factory):
    """Create a test admin user in the database."""
    db = session_factory()
    try:
        repo = UserRepository(db)
        user_data = UserCreate(
            email="admin@example.com",
            username="admin",
            password="adminpass123",
        )
        hashed_password = get_password_hash("adminpass123")
        user = repo.create(user_data, hashed_password)

        # Manually set admin flag (normally would be done through separate endpoint)
        user.is_admin = True
        db.commit()
        db.refresh(user)
        db.expunge(user)
        return user
    finally:
        db.close()


@pytest.fixture
def auth_token(test_user):
    """Create an authentication token for the test user."""
    return create_access_token(data={"sub": str(test_user.id), "username": test_user.username})


@pytest.fixture
def admin_token(test_admin):
    """Create an authentication token for the admin user."""
    return create_access_token(data={"sub": str(test_admin.id), "username": test_admin.username})
