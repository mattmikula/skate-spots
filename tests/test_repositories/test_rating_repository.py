"""Tests for the rating repository."""

import pytest
from uuid import uuid4

from app.models.rating import RatingCreate, RatingUpdate
from app.models.skate_spot import Difficulty, Location, SpotType, SkateSpotCreate
from app.repositories.rating_repository import RatingRepository
from app.repositories.skate_spot_repository import SkateSpotRepository
from app.repositories.user_repository import UserRepository
from app.models.user import UserCreate


@pytest.fixture
def rating_repository(session_factory):
    """Create a rating repository with test session."""
    return RatingRepository(session_factory=session_factory)


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
        email="spotowner@example.com",
        username="spotowner",
        password="password123",
    )
    from app.core.security import get_password_hash
    hashed_password = get_password_hash("password123")
    user = user_repository.create(user_data, hashed_password)

    spot_data = SkateSpotCreate(
        name="Test Spot",
        description="A test spot",
        spot_type=SpotType.PARK,
        difficulty=Difficulty.BEGINNER,
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
        email="rater@example.com",
        username="rater",
        password="password123",
    )
    from app.core.security import get_password_hash
    hashed_password = get_password_hash("password123")
    return user_repository.create(user_data, hashed_password)


def test_create_rating(rating_repository, test_spot, test_user):
    """Test creating a rating."""
    rating_data = RatingCreate(score=5, review="Great spot!")
    rating = rating_repository.create(rating_data, test_spot.id, str(test_user.id))

    assert rating.score == 5
    assert rating.review == "Great spot!"
    assert rating.spot_id == test_spot.id
    assert str(rating.user_id) == str(test_user.id)


def test_get_rating_by_id(rating_repository, test_spot, test_user):
    """Test retrieving a rating by ID."""
    rating_data = RatingCreate(score=4, review="Good spot")
    created_rating = rating_repository.create(rating_data, test_spot.id, str(test_user.id))

    retrieved_rating = rating_repository.get_by_id(created_rating.id)
    assert retrieved_rating is not None
    assert retrieved_rating.id == created_rating.id
    assert retrieved_rating.score == 4


def test_get_rating_by_id_not_found(rating_repository):
    """Test getting a non-existent rating returns None."""
    rating = rating_repository.get_by_id(uuid4())
    assert rating is None


def test_get_rating_by_spot_and_user(rating_repository, test_spot, test_user):
    """Test retrieving a rating by spot and user."""
    rating_data = RatingCreate(score=3, review="Okay spot")
    created_rating = rating_repository.create(rating_data, test_spot.id, str(test_user.id))

    retrieved_rating = rating_repository.get_by_spot_and_user(test_spot.id, str(test_user.id))
    assert retrieved_rating is not None
    assert retrieved_rating.id == created_rating.id


def test_get_ratings_by_spot(rating_repository, test_spot, user_repository):
    """Test retrieving all ratings for a spot."""
    # Create multiple ratings
    ratings_data = [
        RatingCreate(score=5, review="Excellent!"),
        RatingCreate(score=4, review="Good"),
        RatingCreate(score=3, review="Average"),
    ]

    user_data = UserCreate(
        email="rater{id}@example.com",
        username="rater{id}",
        password="password123",
    )
    from app.core.security import get_password_hash
    hashed_password = get_password_hash("password123")

    created_ratings = []
    for i, rating_data in enumerate(ratings_data):
        user_data_i = UserCreate(
            email=f"rater{i}@example.com",
            username=f"rater{i}",
            password="password123",
        )
        user = user_repository.create(user_data_i, hashed_password)
        rating = rating_repository.create(rating_data, test_spot.id, str(user.id))
        created_ratings.append(rating)

    retrieved_ratings = rating_repository.get_by_spot(test_spot.id)
    assert len(retrieved_ratings) == 3
    assert all(r.spot_id == test_spot.id for r in retrieved_ratings)


def test_get_stats_for_spot(rating_repository, test_spot, user_repository):
    """Test getting rating statistics for a spot."""
    from app.core.security import get_password_hash
    hashed_password = get_password_hash("password123")

    # Create ratings with different scores
    scores = [5, 5, 4, 3, 2]
    for i, score in enumerate(scores):
        user_data = UserCreate(
            email=f"statrater{i}@example.com",
            username=f"statrater{i}",
            password="password123",
        )
        user = user_repository.create(user_data, hashed_password)
        rating_data = RatingCreate(score=score, review=f"Rating: {score}")
        rating_repository.create(rating_data, test_spot.id, str(user.id))

    stats = rating_repository.get_stats_for_spot(test_spot.id)

    assert stats.total_ratings == 5
    assert stats.average_score == 3.8  # (5+5+4+3+2) / 5 = 3.8
    assert stats.distribution[5] == 2
    assert stats.distribution[4] == 1
    assert stats.distribution[3] == 1
    assert stats.distribution[2] == 1
    assert stats.distribution[1] == 0


def test_update_rating(rating_repository, test_spot, test_user):
    """Test updating a rating."""
    rating_data = RatingCreate(score=2, review="Needs work")
    created_rating = rating_repository.create(rating_data, test_spot.id, str(test_user.id))

    update_data = RatingUpdate(score=5, review="Actually amazing!")
    updated_rating = rating_repository.update(created_rating.id, update_data)

    assert updated_rating is not None
    assert updated_rating.score == 5
    assert updated_rating.review == "Actually amazing!"


def test_update_rating_partial(rating_repository, test_spot, test_user):
    """Test partially updating a rating."""
    rating_data = RatingCreate(score=3, review="Original review")
    created_rating = rating_repository.create(rating_data, test_spot.id, str(test_user.id))

    update_data = RatingUpdate(score=4)
    updated_rating = rating_repository.update(created_rating.id, update_data)

    assert updated_rating is not None
    assert updated_rating.score == 4
    assert updated_rating.review == "Original review"  # Unchanged


def test_delete_rating(rating_repository, test_spot, test_user):
    """Test deleting a rating."""
    rating_data = RatingCreate(score=1, review="Bad")
    created_rating = rating_repository.create(rating_data, test_spot.id, str(test_user.id))

    success = rating_repository.delete(created_rating.id)
    assert success is True

    retrieved_rating = rating_repository.get_by_id(created_rating.id)
    assert retrieved_rating is None


def test_delete_non_existent_rating(rating_repository):
    """Test deleting a non-existent rating returns False."""
    success = rating_repository.delete(uuid4())
    assert success is False


def test_is_owner(rating_repository, test_spot, test_user, user_repository):
    """Test checking rating ownership."""
    rating_data = RatingCreate(score=5)
    created_rating = rating_repository.create(rating_data, test_spot.id, str(test_user.id))

    from app.core.security import get_password_hash
    hashed_password = get_password_hash("password123")
    other_user_data = UserCreate(
        email="other@example.com",
        username="other",
        password="password123",
    )
    other_user = user_repository.create(other_user_data, hashed_password)

    assert rating_repository.is_owner(created_rating.id, str(test_user.id)) is True
    assert rating_repository.is_owner(created_rating.id, str(other_user.id)) is False
