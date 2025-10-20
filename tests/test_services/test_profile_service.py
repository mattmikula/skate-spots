"""Tests for the profile service."""

from uuid import UUID

import pytest

from app.db.models import SkateSpotORM, UserORM
from app.repositories.profile_repository import ProfileRepository
from app.services.profile_service import ProfileService, UserNotFoundError


@pytest.fixture
def profile_service(session_factory):
    """Create a profile service instance for testing."""
    repo = ProfileRepository(session_factory)
    return ProfileService(repo)


@pytest.fixture
def test_user_orm(session_factory):
    """Create a test user in the database."""
    with session_factory() as session:
        user = UserORM(
            email="profile_test@example.com",
            username="profiletester",
            hashed_password="hashed_pw",
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


def test_get_profile_by_username(profile_service, test_user_orm):
    """Test retrieving a profile by username."""
    profile = profile_service.get_profile_by_username(test_user_orm.username)

    assert profile.user.username == test_user_orm.username
    assert profile.user.id == UUID(test_user_orm.id)
    assert profile.statistics.spots_added == 0
    assert profile.statistics.photos_uploaded == 0
    assert profile.statistics.comments_posted == 0
    assert profile.statistics.ratings_given == 0


def test_get_profile_by_id(profile_service, test_user_orm):
    """Test retrieving a profile by user ID."""
    profile = profile_service.get_profile_by_id(test_user_orm.id)

    assert profile.user.username == test_user_orm.username
    assert profile.user.id == UUID(test_user_orm.id)


def test_get_profile_nonexistent_username(profile_service):
    """Test that requesting a non-existent username raises an error."""
    with pytest.raises(UserNotFoundError):
        profile_service.get_profile_by_username("nonexistent_user")


def test_get_profile_nonexistent_id(profile_service):
    """Test that requesting a non-existent user ID raises an error."""
    with pytest.raises(UserNotFoundError):
        profile_service.get_profile_by_id("00000000-0000-0000-0000-000000000000")


def test_profile_with_spots(profile_service, session_factory, test_user_orm):
    """Test that profile includes spots added by the user."""
    # Create a spot for the user
    with session_factory() as session:
        spot = SkateSpotORM(
            name="Test Spot",
            description="A test spot",
            spot_type="park",
            difficulty="beginner",
            latitude=40.7128,
            longitude=-74.0060,
            city="New York",
            country="USA",
            user_id=test_user_orm.id,
        )
        session.add(spot)
        session.commit()

    profile = profile_service.get_profile_by_username(test_user_orm.username)

    assert profile.statistics.spots_added == 1
    assert len(profile.recent_spots) == 1
    assert profile.recent_spots[0].name == "Test Spot"


def test_profile_activity_feed(profile_service, session_factory, test_user_orm):
    """Test that profile includes activity feed."""
    # Create a spot for the user
    with session_factory() as session:
        spot = SkateSpotORM(
            name="Activity Test Spot",
            description="A test spot for activity feed",
            spot_type="street",
            difficulty="intermediate",
            latitude=51.5074,
            longitude=-0.1278,
            city="London",
            country="UK",
            user_id=test_user_orm.id,
        )
        session.add(spot)
        session.commit()

    profile = profile_service.get_profile_by_username(test_user_orm.username)

    assert len(profile.activity.activities) > 0
    assert profile.activity.activities[0].activity_type == "spot_created"
    assert profile.activity.activities[0].spot_name == "Activity Test Spot"
