"""Tests for the rating service."""

import pytest

from app.core.security import get_password_hash
from app.models.rating import RatingCreate, RatingUpdate
from app.models.skate_spot import Difficulty, Location, SkateSpotCreate, SpotType
from app.models.user import UserCreate
from app.repositories.rating_repository import RatingRepository
from app.repositories.skate_spot_repository import SkateSpotRepository
from app.repositories.user_repository import UserRepository
from app.services.rating_service import RatingService


@pytest.fixture
def rating_service(session_factory):
    """Create a rating service with test session."""
    repository = RatingRepository(session_factory=session_factory)
    return RatingService(repository)


@pytest.fixture
def skate_spot_repository(session_factory):
    """Create a skate spot repository with test session."""
    return SkateSpotRepository(session_factory=session_factory)


@pytest.fixture
def user_repository(session_factory):
    """Create a user repository with test session."""
    db = session_factory()
    try:
        return UserRepository(db)
    finally:
        db.close()


@pytest.fixture
def test_spot(skate_spot_repository, user_repository):
    """Create a test skate spot."""
    user_data = UserCreate(
        email="servicespotowner@example.com",
        username="servicespotowner",
        password="password123",
    )
    hashed_password = get_password_hash("password123")
    user = user_repository.create(user_data, hashed_password)

    spot_data = SkateSpotCreate(
        name="Service Test Spot",
        description="A service test spot",
        spot_type=SpotType.PARK,
        difficulty=Difficulty.INTERMEDIATE,
        location=Location(
            latitude=40.7128,
            longitude=-74.0060,
            city="New York",
            country="USA",
        ),
    )
    return skate_spot_repository.create(spot_data, str(user.id))


@pytest.fixture
def test_user(user_repository):
    """Create a test user for ratings."""
    user_data = UserCreate(
        email="servicerater@example.com",
        username="servicerater",
        password="password123",
    )
    hashed_password = get_password_hash("password123")
    return user_repository.create(user_data, hashed_password)


def test_create_rating(rating_service, test_spot, test_user):
    """Test creating a rating through service."""
    rating_data = RatingCreate(score=5, review="Excellent spot!")
    rating = rating_service.create_rating(test_spot.id, str(test_user.id), rating_data)

    assert rating.score == 5
    assert rating.review == "Excellent spot!"


def test_get_rating(rating_service, test_spot, test_user):
    """Test retrieving a rating through service."""
    rating_data = RatingCreate(score=4)
    created_rating = rating_service.create_rating(test_spot.id, str(test_user.id), rating_data)

    retrieved_rating = rating_service.get_rating(created_rating.id)
    assert retrieved_rating is not None
    assert retrieved_rating.id == created_rating.id


def test_get_user_rating_for_spot(rating_service, test_spot, test_user):
    """Test getting a user's rating for a specific spot."""
    rating_data = RatingCreate(score=3)
    created_rating = rating_service.create_rating(test_spot.id, str(test_user.id), rating_data)

    retrieved_rating = rating_service.get_user_rating_for_spot(test_spot.id, str(test_user.id))
    assert retrieved_rating is not None
    assert retrieved_rating.id == created_rating.id
    assert retrieved_rating.score == 3


def test_get_spot_ratings(rating_service, test_spot, user_repository):
    """Test getting all ratings for a spot."""
    hashed_password = get_password_hash("password123")

    ratings_scores = [5, 4, 3]
    for i, score in enumerate(ratings_scores):
        user_data = UserCreate(
            email=f"servicemulti{i}@example.com",
            username=f"servicemulti{i}",
            password="password123",
        )
        user = user_repository.create(user_data, hashed_password)
        rating_data = RatingCreate(score=score)
        rating_service.create_rating(test_spot.id, str(user.id), rating_data)

    ratings = rating_service.get_spot_ratings(test_spot.id)
    assert len(ratings) == 3
    assert all(r.spot_id == test_spot.id for r in ratings)


def test_get_spot_rating_stats(rating_service, test_spot, user_repository):
    """Test getting rating statistics."""
    hashed_password = get_password_hash("password123")

    scores = [5, 5, 4, 3, 2]
    for i, score in enumerate(scores):
        user_data = UserCreate(
            email=f"servicestat{i}@example.com",
            username=f"servicestat{i}",
            password="password123",
        )
        user = user_repository.create(user_data, hashed_password)
        rating_data = RatingCreate(score=score)
        rating_service.create_rating(test_spot.id, str(user.id), rating_data)

    stats = rating_service.get_spot_rating_stats(test_spot.id)
    assert stats.total_ratings == 5
    assert stats.average_score == 3.8


def test_update_rating(rating_service, test_spot, test_user):
    """Test updating a rating through service."""
    rating_data = RatingCreate(score=2, review="Meh")
    created_rating = rating_service.create_rating(test_spot.id, str(test_user.id), rating_data)

    update_data = RatingUpdate(score=5, review="Changed my mind!")
    updated_rating = rating_service.update_rating(created_rating.id, update_data)

    assert updated_rating is not None
    assert updated_rating.score == 5
    assert updated_rating.review == "Changed my mind!"


def test_delete_rating(rating_service, test_spot, test_user):
    """Test deleting a rating through service."""
    rating_data = RatingCreate(score=1)
    created_rating = rating_service.create_rating(test_spot.id, str(test_user.id), rating_data)

    success = rating_service.delete_rating(created_rating.id)
    assert success is True

    retrieved_rating = rating_service.get_rating(created_rating.id)
    assert retrieved_rating is None


def test_is_owner(rating_service, test_spot, test_user, user_repository):
    """Test checking ownership through service."""
    rating_data = RatingCreate(score=5)
    created_rating = rating_service.create_rating(test_spot.id, str(test_user.id), rating_data)

    hashed_password = get_password_hash("password123")
    other_user_data = UserCreate(
        email="serviceother@example.com",
        username="serviceother",
        password="password123",
    )
    other_user = user_repository.create(other_user_data, hashed_password)

    assert rating_service.is_owner(created_rating.id, str(test_user.id)) is True
    assert rating_service.is_owner(created_rating.id, str(other_user.id)) is False
