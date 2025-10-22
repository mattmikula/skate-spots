"""Shared test fixtures and configuration."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.dependencies import get_user_repository
from app.core.rate_limiter import rate_limiter
from app.core.security import create_access_token, get_password_hash
from app.db.database import Base, get_db
from app.models.user import UserCreate
from app.repositories.comment_repository import CommentRepository
from app.repositories.favorite_repository import FavoriteRepository
from app.repositories.rating_repository import RatingRepository
from app.repositories.skate_spot_repository import SkateSpotRepository
from app.repositories.user_profile_repository import UserProfileRepository
from app.repositories.user_repository import UserRepository
from app.services.comment_service import CommentService, get_comment_service
from app.services.favorite_service import FavoriteService, get_favorite_service
from app.services.rating_service import (
    RatingService,
    get_rating_service,
)
from app.services.skate_spot_service import (
    SkateSpotService,
    get_skate_spot_service,
)
from app.services.user_profile_service import (
    UserProfileService,
    get_user_profile_service,
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
    rating_repository = RatingRepository(session_factory=session_factory)
    rating_service = RatingService(rating_repository, repository)
    comment_repository = CommentRepository(session_factory=session_factory)
    comment_service = CommentService(comment_repository, repository)
    favorite_repository = FavoriteRepository(session_factory=session_factory)
    favorite_service = FavoriteService(favorite_repository, repository)
    profile_repository = UserProfileRepository(session_factory=session_factory)
    profile_service = UserProfileService(profile_repository)

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
    app.dependency_overrides[get_rating_service] = lambda: rating_service
    app.dependency_overrides[get_comment_service] = lambda: comment_service
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_user_repository] = override_get_user_repository
    app.dependency_overrides[get_favorite_service] = lambda: favorite_service
    app.dependency_overrides[get_user_profile_service] = lambda: profile_service

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_skate_spot_service, None)
        app.dependency_overrides.pop(get_rating_service, None)
        app.dependency_overrides.pop(get_comment_service, None)
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_user_repository, None)
        app.dependency_overrides.pop(get_favorite_service, None)
        app.dependency_overrides.pop(get_user_profile_service, None)


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


@pytest.fixture
def db(session_factory):
    """Provide a database session for repository tests."""
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def users(db):
    """Create test users for testing."""
    user_repo = UserRepository(db)
    user1_data = UserCreate(
        email="user1@example.com",
        username="user1",
        password="password123",
    )
    user2_data = UserCreate(
        email="user2@example.com",
        username="user2",
        password="password123",
    )
    user3_data = UserCreate(
        email="user3@example.com",
        username="user3",
        password="password123",
    )

    hashed_password = get_password_hash("password123")
    user1 = user_repo.create(user1_data, hashed_password)
    user2 = user_repo.create(user2_data, hashed_password)
    user3 = user_repo.create(user3_data, hashed_password)

    db.commit()
    db.refresh(user1)
    db.refresh(user2)
    db.refresh(user3)

    return user1, user2, user3
