"""Tests for the favourite spots repository."""

from uuid import uuid4

import pytest

from app.core.security import get_password_hash
from app.models.skate_spot import Difficulty, Location, SkateSpotCreate, SpotType
from app.models.user import UserCreate
from app.repositories.favorite_repository import FavoriteRepository
from app.repositories.skate_spot_repository import SkateSpotRepository
from app.repositories.user_repository import UserRepository


@pytest.fixture
def favorite_repository(session_factory):
    return FavoriteRepository(session_factory=session_factory)


@pytest.fixture
def skate_spot_repository(session_factory):
    return SkateSpotRepository(session_factory=session_factory)


@pytest.fixture
def sample_user_id(session_factory):
    db = session_factory()
    try:
        repo = UserRepository(db)
        user = repo.create(
            UserCreate(
                email="favorite@example.com",
                username="favorite_user",
                password="changeme123",
            ),
            get_password_hash("changeme123"),
        )
        db.expunge(user)
        return user.id
    finally:
        db.close()


@pytest.fixture
def sample_spot(skate_spot_repository):
    payload = SkateSpotCreate(
        name="Favourite Test Spot",
        description="Spot used for favourite repository tests",
        spot_type=SpotType.STREET,
        difficulty=Difficulty.BEGINNER,
        location=Location(
            latitude=40.7128,
            longitude=-74.006,
            city="New York",
            country="USA",
        ),
        is_public=True,
        requires_permission=False,
    )
    owner_id = str(uuid4())
    return skate_spot_repository.create(payload, user_id=owner_id)


def test_add_and_exists(favorite_repository, sample_user_id, sample_spot):
    favorite_repository.add(sample_user_id, sample_spot.id)
    assert favorite_repository.exists(sample_user_id, sample_spot.id) is True


def test_remove_favorite(favorite_repository, sample_user_id, sample_spot):
    favorite_repository.add(sample_user_id, sample_spot.id)
    removed = favorite_repository.remove(sample_user_id, sample_spot.id)
    assert removed is True
    assert favorite_repository.exists(sample_user_id, sample_spot.id) is False


def test_list_spot_ids_returns_recency_order(
    favorite_repository,
    sample_user_id,
    sample_spot,
    skate_spot_repository,
):
    another_spot = skate_spot_repository.create(
        SkateSpotCreate(
            name="Secondary Spot",
            description="Another spot",
            spot_type=SpotType.PARK,
            difficulty=Difficulty.INTERMEDIATE,
            location=Location(
                latitude=34.0522,
                longitude=-118.2437,
                city="Los Angeles",
                country="USA",
            ),
            is_public=True,
            requires_permission=False,
        ),
        user_id=str(uuid4()),
    )

    favorite_repository.add(sample_user_id, sample_spot.id)
    favorite_repository.add(sample_user_id, another_spot.id)

    spot_ids = favorite_repository.list_spot_ids_for_user(sample_user_id)
    assert spot_ids[0] == another_spot.id
    assert spot_ids[1] == sample_spot.id
