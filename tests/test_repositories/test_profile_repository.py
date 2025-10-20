"""Tests for the profile repository."""

import pytest

from app.db.models import RatingORM, SkateSpotORM, SpotCommentORM, UserORM
from app.repositories.profile_repository import ProfileRepository


@pytest.fixture
def profile_repo(session_factory):
    """Create a profile repository instance for testing."""
    return ProfileRepository(session_factory)


@pytest.fixture
def test_user_orm(session_factory):
    """Create a test user in the database."""
    with session_factory() as session:
        user = UserORM(
            email="repo_test@example.com",
            username="repotester",
            hashed_password="hashed_pw",
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


def test_get_user_by_username(profile_repo, test_user_orm):
    """Test retrieving a user by username."""
    user = profile_repo.get_user_by_username(test_user_orm.username)
    assert user is not None
    assert user.username == test_user_orm.username


def test_get_user_by_id(profile_repo, test_user_orm):
    """Test retrieving a user by ID."""
    user = profile_repo.get_user_by_id(test_user_orm.id)
    assert user is not None
    assert user.id == test_user_orm.id


def test_get_nonexistent_user(profile_repo):
    """Test that requesting a non-existent user returns None."""
    user = profile_repo.get_user_by_username("nonexistent")
    assert user is None


def test_get_user_statistics_empty(profile_repo, test_user_orm):
    """Test getting statistics for a user with no activity."""
    stats = profile_repo.get_user_statistics(test_user_orm.id)

    assert stats.spots_added == 0
    assert stats.photos_uploaded == 0
    assert stats.comments_posted == 0
    assert stats.ratings_given == 0


def test_get_user_statistics_with_spots(profile_repo, session_factory, test_user_orm):
    """Test getting statistics for a user with spots."""
    with session_factory() as session:
        spot = SkateSpotORM(
            name="Stats Test Spot",
            description="For statistics testing",
            spot_type="ledge",
            difficulty="advanced",
            latitude=48.8566,
            longitude=2.3522,
            city="Paris",
            country="France",
            user_id=test_user_orm.id,
        )
        session.add(spot)
        session.commit()

    stats = profile_repo.get_user_statistics(test_user_orm.id)
    assert stats.spots_added == 1


def test_get_user_statistics_with_comments(profile_repo, session_factory, test_user_orm):
    """Test getting statistics for a user with comments."""
    with session_factory() as session:
        # Create a spot first
        spot = SkateSpotORM(
            name="Comment Test Spot",
            description="For comment testing",
            spot_type="bowl",
            difficulty="expert",
            latitude=35.6762,
            longitude=139.6503,
            city="Tokyo",
            country="Japan",
            user_id=test_user_orm.id,
        )
        session.add(spot)
        session.commit()
        session.refresh(spot)

        # Create a comment
        comment = SpotCommentORM(
            spot_id=spot.id,
            user_id=test_user_orm.id,
            content="This is a test comment.",
        )
        session.add(comment)
        session.commit()

    stats = profile_repo.get_user_statistics(test_user_orm.id)
    assert stats.comments_posted == 1


def test_get_user_statistics_with_ratings(profile_repo, session_factory, test_user_orm):
    """Test getting statistics for a user with ratings."""
    with session_factory() as session:
        # Create a spot first
        spot = SkateSpotORM(
            name="Rating Test Spot",
            description="For rating testing",
            spot_type="vert",
            difficulty="expert",
            latitude=-33.8688,
            longitude=151.2093,
            city="Sydney",
            country="Australia",
            user_id=test_user_orm.id,
        )
        session.add(spot)
        session.commit()
        session.refresh(spot)

        # Create a rating
        rating = RatingORM(
            spot_id=spot.id,
            user_id=test_user_orm.id,
            score=5,
            comment="Amazing spot!",
        )
        session.add(rating)
        session.commit()

    stats = profile_repo.get_user_statistics(test_user_orm.id)
    assert stats.ratings_given == 1


def test_get_recent_spots(profile_repo, session_factory, test_user_orm):
    """Test retrieving recent spots for a user."""
    with session_factory() as session:
        # Create multiple spots
        for i in range(3):
            spot = SkateSpotORM(
                name=f"Recent Spot {i}",
                description=f"Recent spot number {i}",
                spot_type="rail",
                difficulty="intermediate",
                latitude=40.7128 + i,
                longitude=-74.0060 + i,
                city="Test City",
                country="Test Country",
                user_id=test_user_orm.id,
            )
            session.add(spot)
        session.commit()

    recent_spots = profile_repo.get_recent_spots(test_user_orm.id, limit=2)
    assert len(recent_spots) == 2
    # Should be ordered by created_at desc
    assert recent_spots[0].name == "Recent Spot 2"


def test_get_recent_comments(profile_repo, session_factory, test_user_orm):
    """Test retrieving recent comments for a user."""
    with session_factory() as session:
        # Create a spot
        spot = SkateSpotORM(
            name="Comment Spot",
            description="Spot for comments",
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
        session.refresh(spot)

        # Create comments
        for i in range(2):
            comment = SpotCommentORM(
                spot_id=spot.id,
                user_id=test_user_orm.id,
                content=f"Comment {i}",
            )
            session.add(comment)
        session.commit()

    recent_comments = profile_repo.get_recent_comments(test_user_orm.id, limit=5)
    assert len(recent_comments) == 2


def test_get_user_activity(profile_repo, session_factory, test_user_orm):
    """Test retrieving user activity."""
    with session_factory() as session:
        spot = SkateSpotORM(
            name="Activity Spot",
            description="Spot for activity",
            spot_type="stairs",
            difficulty="advanced",
            latitude=37.7749,
            longitude=-122.4194,
            city="San Francisco",
            country="USA",
            user_id=test_user_orm.id,
        )
        session.add(spot)
        session.commit()

    activities = profile_repo.get_user_activity(test_user_orm.id, limit=10)
    assert len(activities) > 0
    assert activities[0].activity_type == "spot_created"
