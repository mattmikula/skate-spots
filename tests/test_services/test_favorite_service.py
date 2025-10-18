"""Tests for the favourite service layer."""

from uuid import uuid4

import pytest

from app.core.security import get_password_hash
from app.models.favorite import FavoriteStatus
from app.models.skate_spot import Difficulty, Location, SkateSpot, SkateSpotCreate, SpotType
from app.models.user import UserCreate
from app.repositories.favorite_repository import FavoriteRepository
from app.repositories.skate_spot_repository import SkateSpotRepository
from app.repositories.user_repository import UserRepository
from app.services.favorite_service import FavoriteService, SpotNotFoundError


@pytest.fixture
def favorite_service(session_factory):
    skate_repo = SkateSpotRepository(session_factory=session_factory)
    favorite_repo = FavoriteRepository(session_factory=session_factory)
    service = FavoriteService(favorite_repo, skate_repo)
    return service, skate_repo


@pytest.fixture
def user_id(session_factory):
    db = session_factory()
    try:
        repo = UserRepository(db)
        user = repo.create(
            UserCreate(
                email="svc-fav@example.com",
                username="svc_fav",
                password="password123",
            ),
            get_password_hash("password123"),
        )
        db.expunge(user)
        return user.id
    finally:
        db.close()


def create_spot(skate_repo: SkateSpotRepository) -> SkateSpot:
    data = SkateSpotCreate(
        name="Service Favourite Spot",
        description="Used in favourite service tests",
        spot_type=SpotType.BOWL,
        difficulty=Difficulty.ADVANCED,
        location=Location(
            latitude=51.5074,
            longitude=-0.1278,
            city="London",
            country="United Kingdom",
        ),
        is_public=True,
        requires_permission=False,
    )
    owner_id = str(uuid4())
    return skate_repo.create(data, owner_id)


def test_add_favorite_marks_spot(favorite_service, user_id):
    service, skate_repo = favorite_service
    spot = create_spot(skate_repo)

    status = service.add_favorite(spot.id, user_id)

    assert isinstance(status, FavoriteStatus)
    assert status.is_favorite is True
    assert status.spot_id == spot.id


def test_remove_favorite_unmarks_spot(favorite_service, user_id):
    service, skate_repo = favorite_service
    spot = create_spot(skate_repo)
    service.add_favorite(spot.id, user_id)

    status = service.remove_favorite(spot.id, user_id)

    assert status.is_favorite is False


def test_toggle_favorite_flips_state(favorite_service, user_id):
    service, skate_repo = favorite_service
    spot = create_spot(skate_repo)

    first = service.toggle_favorite(spot.id, user_id)
    second = service.toggle_favorite(spot.id, user_id)

    assert first.is_favorite is True
    assert second.is_favorite is False


def test_list_user_favorites_returns_spots(favorite_service, user_id):
    service, skate_repo = favorite_service
    spot_one = create_spot(skate_repo)
    spot_two = create_spot(skate_repo)

    service.add_favorite(spot_one.id, user_id)
    service.add_favorite(spot_two.id, user_id)

    favourites = service.list_user_favorites(user_id)

    assert len(favourites) == 2
    assert {spot.id for spot in favourites} == {spot_one.id, spot_two.id}


def test_toggle_missing_spot_raises(favorite_service, user_id):
    service, _ = favorite_service
    with pytest.raises(SpotNotFoundError):
        service.toggle_favorite(uuid4(), user_id)
