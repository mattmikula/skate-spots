"""Tests for the rating service."""

from uuid import uuid4

import pytest

from app.models.rating import RatingCreate
from app.models.skate_spot import Difficulty, Location, SkateSpotCreate, SpotType
from app.repositories.rating_repository import RatingRepository
from app.repositories.skate_spot_repository import SkateSpotRepository
from app.services.rating_service import (
    RatingNotFoundError,
    RatingService,
    SpotNotFoundError,
)


@pytest.fixture
def spot_repository(session_factory):
    """Provide a skate spot repository bound to the in-memory database."""

    return SkateSpotRepository(session_factory=session_factory)


@pytest.fixture
def rating_service(session_factory, spot_repository):
    """Provide a rating service configured with in-memory repositories."""

    rating_repository = RatingRepository(session_factory=session_factory)
    return RatingService(rating_repository, spot_repository)


@pytest.fixture
def sample_spot(spot_repository):
    """Create a sample spot for service tests."""

    spot_data = SkateSpotCreate(
        name="Service Rating Spot",
        description="Spot used for testing rating service",
        spot_type=SpotType.STREET,
        difficulty=Difficulty.BEGINNER,
        location=Location(
            latitude=48.8566,
            longitude=2.3522,
            city="Paris",
            country="France",
        ),
        is_public=True,
        requires_permission=False,
    )
    owner_id = str(uuid4())
    return spot_repository.create(spot_data, user_id=owner_id)


def test_set_and_get_rating(rating_service, sample_spot):
    """Service can create and retrieve a rating with summary metadata."""

    user_id = str(uuid4())
    summary = rating_service.set_rating(
        sample_spot.id,
        user_id=user_id,
        rating_data=RatingCreate(score=5, comment="Amazing"),
    )

    assert summary.average_score == 5.0
    assert summary.ratings_count == 1
    assert summary.user_rating is not None
    assert summary.user_rating.score == 5

    rating = rating_service.get_user_rating(sample_spot.id, user_id)
    assert rating.score == 5
    assert rating.comment == "Amazing"


def test_set_rating_updates_existing_entry(rating_service, sample_spot):
    """Setting a rating twice updates the existing record."""

    user_id = str(uuid4())
    rating_service.set_rating(
        sample_spot.id,
        user_id=user_id,
        rating_data=RatingCreate(score=3, comment=None),
    )

    summary = rating_service.set_rating(
        sample_spot.id,
        user_id=user_id,
        rating_data=RatingCreate(score=4, comment="Improved"),
    )

    assert summary.average_score == 4.0
    assert summary.ratings_count == 1
    assert summary.user_rating is not None
    assert summary.user_rating.comment == "Improved"


def test_get_summary_includes_optional_user_rating(rating_service, sample_spot):
    """Summary includes user rating when user_id is provided."""

    user_id = str(uuid4())
    rating_service.set_rating(
        sample_spot.id,
        user_id=user_id,
        rating_data=RatingCreate(score=4, comment=None),
    )

    summary = rating_service.get_summary(sample_spot.id, user_id=user_id)
    assert summary.user_rating is not None
    assert summary.user_rating.score == 4
    assert summary.average_score == 4.0
    assert summary.ratings_count == 1


def test_delete_rating(rating_service, sample_spot):
    """Deleting a rating removes it and returns the updated summary."""

    user_id = str(uuid4())
    rating_service.set_rating(
        sample_spot.id,
        user_id=user_id,
        rating_data=RatingCreate(score=2, comment=None),
    )

    summary = rating_service.delete_rating(sample_spot.id, user_id)
    assert summary.ratings_count == 0
    assert summary.average_score is None
    assert summary.user_rating is None

    with pytest.raises(RatingNotFoundError):
        rating_service.get_user_rating(sample_spot.id, user_id)


def test_delete_missing_rating_raises(rating_service, sample_spot):
    """Deleting a missing rating raises an error."""

    with pytest.raises(RatingNotFoundError):
        rating_service.delete_rating(sample_spot.id, str(uuid4()))


def test_missing_rating_raises_for_get(rating_service, sample_spot):
    """Attempting to fetch a missing rating raises an error."""

    with pytest.raises(RatingNotFoundError):
        rating_service.get_user_rating(sample_spot.id, str(uuid4()))


def test_set_rating_for_missing_spot_raises(rating_service):
    """Setting a rating for a missing spot raises an exception."""

    missing_spot_id = uuid4()
    with pytest.raises(SpotNotFoundError):
        rating_service.set_rating(
            missing_spot_id,
            user_id=str(uuid4()),
            rating_data=RatingCreate(score=4, comment=None),
        )
