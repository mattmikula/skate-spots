"""Tests for the rating repository."""

from uuid import UUID, uuid4

import pytest

from app.models.rating import RatingCreate
from app.models.skate_spot import Difficulty, Location, SkateSpotCreate, SpotType
from app.repositories.rating_repository import RatingRepository
from app.repositories.skate_spot_repository import SkateSpotRepository


@pytest.fixture
def rating_repository(session_factory):
    """Return a rating repository bound to the in-memory database."""

    return RatingRepository(session_factory=session_factory)


@pytest.fixture
def skate_spot_repository(session_factory):
    """Return a skate spot repository bound to the in-memory database."""

    return SkateSpotRepository(session_factory=session_factory)


@pytest.fixture
def sample_spot(skate_spot_repository):
    """Create a sample skate spot for rating tests."""

    spot_data = SkateSpotCreate(
        name="Rating Test Spot",
        description="Spot used for rating repository tests",
        spot_type=SpotType.PARK,
        difficulty=Difficulty.INTERMEDIATE,
        location=Location(
            latitude=37.7749,
            longitude=-122.4194,
            city="San Francisco",
            country="USA",
        ),
        is_public=True,
        requires_permission=False,
    )
    owner_id = str(uuid4())
    return skate_spot_repository.create(spot_data, user_id=owner_id)


def test_initial_summary_is_empty(rating_repository, sample_spot):
    """Ratings summary reports zero count and no average when no ratings exist."""

    summary = rating_repository.get_summary(sample_spot.id)
    assert summary.ratings_count == 0
    assert summary.average_score is None


def test_upsert_creates_rating(rating_repository, sample_spot):
    """Upserting a rating creates it when none exist."""

    rating_data = RatingCreate(score=4, comment="Great flow")
    user_id = str(uuid4())
    rating = rating_repository.upsert(sample_spot.id, user_id=user_id, rating_data=rating_data)

    assert rating.score == 4
    assert rating.comment == "Great flow"
    assert isinstance(rating.user_id, UUID)
    assert rating.user_id == UUID(user_id)

    summary = rating_repository.get_summary(sample_spot.id)
    assert summary.ratings_count == 1
    assert summary.average_score == 4.0


def test_upsert_updates_existing_rating(rating_repository, sample_spot):
    """Upserting a rating updates an existing entry for the same user."""

    user_id = str(uuid4())
    rating_repository.upsert(
        sample_spot.id,
        user_id=user_id,
        rating_data=RatingCreate(score=3, comment="Initial"),
    )

    updated = rating_repository.upsert(
        sample_spot.id,
        user_id=user_id,
        rating_data=RatingCreate(score=5, comment="Updated"),
    )

    assert updated.score == 5
    assert updated.comment == "Updated"

    summary = rating_repository.get_summary(sample_spot.id)
    assert summary.ratings_count == 1
    assert summary.average_score == 5.0


def test_get_user_rating(rating_repository, sample_spot):
    """Repository returns the user's rating when it exists."""

    user_id = str(uuid4())
    rating_repository.upsert(
        sample_spot.id,
        user_id=user_id,
        rating_data=RatingCreate(score=2, comment=None),
    )

    rating = rating_repository.get_user_rating(sample_spot.id, user_id)
    assert rating is not None
    assert rating.score == 2
    assert rating.comment is None


def test_get_user_rating_missing_returns_none(rating_repository, sample_spot):
    """Repository returns None when a user has not rated a spot."""

    rating = rating_repository.get_user_rating(sample_spot.id, str(uuid4()))
    assert rating is None


def test_delete_rating(rating_repository, sample_spot):
    """Deleting a rating removes it and updates the summary."""

    user_id = str(uuid4())
    rating_repository.upsert(
        sample_spot.id,
        user_id=user_id,
        rating_data=RatingCreate(score=4, comment=None),
    )

    deleted = rating_repository.delete_rating(sample_spot.id, user_id)
    assert deleted is True

    summary = rating_repository.get_summary(sample_spot.id)
    assert summary.ratings_count == 0
    assert summary.average_score is None


def test_delete_rating_missing_returns_false(rating_repository, sample_spot):
    """Deleting a rating that does not exist returns False."""

    deleted = rating_repository.delete_rating(sample_spot.id, str(uuid4()))
    assert deleted is False


def test_summary_across_multiple_ratings(rating_repository, sample_spot):
    """Summary aggregates multiple user ratings."""

    rating_repository.upsert(
        sample_spot.id,
        user_id=str(uuid4()),
        rating_data=RatingCreate(score=4, comment=None),
    )
    rating_repository.upsert(
        sample_spot.id,
        user_id=str(uuid4()),
        rating_data=RatingCreate(score=2, comment=None),
    )

    summary = rating_repository.get_summary(sample_spot.id)
    assert summary.ratings_count == 2
    assert summary.average_score == 3.0
