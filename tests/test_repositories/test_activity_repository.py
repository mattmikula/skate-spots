"""Tests for the activity repository."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from app.db.models import UserFollowORM, UserORM
from app.repositories.activity_repository import ActivityRepository

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


@pytest.fixture
def activity_repo(db: Session) -> ActivityRepository:
    """Create an activity repository instance."""
    return ActivityRepository(db)


@pytest.fixture
def users(db: Session) -> tuple[UserORM, UserORM, UserORM]:
    """Create test users."""
    user1 = UserORM(
        email="user1@example.com",
        username="user1",
        hashed_password="hashedpassword1",
    )
    user2 = UserORM(
        email="user2@example.com",
        username="user2",
        hashed_password="hashedpassword2",
    )
    user3 = UserORM(
        email="user3@example.com",
        username="user3",
        hashed_password="hashedpassword3",
    )
    db.add(user1)
    db.add(user2)
    db.add(user3)
    db.commit()
    return user1, user2, user3


class TestActivityRepository:
    """Test cases for ActivityRepository."""

    def test_create_activity(
        self, activity_repo: ActivityRepository, users: tuple[UserORM, UserORM, UserORM]
    ):
        """Test creating a new activity."""
        user1, _, _ = users

        activity = activity_repo.create_activity(
            user_id=user1.id,
            activity_type="spot_created",
            target_type="spot",
            target_id="spot123",
            metadata={"spot_name": "Test Spot"},
        )

        assert activity is not None
        assert activity.user_id == user1.id
        assert activity.activity_type == "spot_created"
        assert activity.target_type == "spot"
        assert activity.target_id == "spot123"

        # Verify metadata was stored
        metadata = json.loads(activity.activity_metadata)
        assert metadata["spot_name"] == "Test Spot"

    def test_create_activity_no_metadata(
        self, activity_repo: ActivityRepository, users: tuple[UserORM, UserORM, UserORM]
    ):
        """Test creating activity without metadata."""
        user1, _, _ = users

        activity = activity_repo.create_activity(
            user_id=user1.id,
            activity_type="spot_rated",
            target_type="rating",
            target_id="rating123",
        )

        assert activity is not None
        assert activity.activity_metadata is None

    def test_get_public_feed(
        self, activity_repo: ActivityRepository, users: tuple[UserORM, UserORM, UserORM]
    ):
        """Test getting public feed."""
        user1, user2, user3 = users

        # Create activities from different users
        activity_repo.create_activity(user1.id, "spot_created", "spot", "spot1")
        activity_repo.create_activity(user2.id, "spot_rated", "rating", "rating1")
        activity_repo.create_activity(user3.id, "spot_favorited", "favorite", "fav1")

        activities, total = activity_repo.get_public_feed(limit=10, offset=0)

        assert total == 3
        assert len(activities) == 3

    def test_get_user_feed_follows(
        self,
        db: Session,
        activity_repo: ActivityRepository,
        users: tuple[UserORM, UserORM, UserORM],
    ):
        """Test getting personalized feed based on follows."""
        user1, user2, user3 = users

        # user1 follows user2 and user3
        follow1 = UserFollowORM(follower_id=user1.id, following_id=user2.id)
        follow2 = UserFollowORM(follower_id=user1.id, following_id=user3.id)
        db.add(follow1)
        db.add(follow2)
        db.commit()

        # Create activities
        activity_repo.create_activity(user2.id, "spot_created", "spot", "spot1")  # Should appear
        activity_repo.create_activity(user3.id, "spot_rated", "rating", "rating1")  # Should appear
        activity_repo.create_activity(
            user1.id, "spot_commented", "comment", "comment1"
        )  # Should NOT appear (own activity)

        # Create activity from user not followed
        user4 = UserORM(
            email="user4@example.com",
            username="user4",
            hashed_password="hashedpassword4",
        )
        db.add(user4)
        db.commit()
        activity_repo.create_activity(
            user4.id, "spot_favorited", "favorite", "fav1"
        )  # Should NOT appear

        activities, total = activity_repo.get_user_feed(user1.id, limit=10, offset=0)

        assert total == 2
        assert len(activities) == 2

    def test_get_user_activity(
        self, activity_repo: ActivityRepository, users: tuple[UserORM, UserORM, UserORM]
    ):
        """Test getting activity history for a specific user."""
        user1, user2, _ = users

        activity_repo.create_activity(user1.id, "spot_created", "spot", "spot1")
        activity_repo.create_activity(user1.id, "spot_rated", "rating", "rating1")
        activity_repo.create_activity(user2.id, "spot_commented", "comment", "comment1")

        activities, total = activity_repo.get_user_activity(user1.id, limit=10, offset=0)

        assert total == 2
        assert len(activities) == 2
        assert all(a.user_id == user1.id for a in activities)

    def test_delete_activity_by_target(
        self, activity_repo: ActivityRepository, users: tuple[UserORM, UserORM, UserORM]
    ):
        """Test deleting activities by target."""
        user1, user2, _ = users

        activity_repo.create_activity(user1.id, "spot_created", "spot", "spot1")
        activity_repo.create_activity(user1.id, "spot_rated", "rating", "spot1_rating")
        activity_repo.create_activity(user2.id, "spot_favorited", "favorite", "spot2_fav")

        # Delete all spot_created activities with target spot1
        deleted_count = activity_repo.delete_activity_by_target("spot", "spot1")

        assert deleted_count == 1

        # Verify other activities still exist
        activities, total = activity_repo.get_public_feed(limit=10, offset=0)
        assert total == 2

    def test_get_activity_by_id(
        self, activity_repo: ActivityRepository, users: tuple[UserORM, UserORM, UserORM]
    ):
        """Test getting a single activity by ID."""
        user1, _, _ = users

        created = activity_repo.create_activity(
            user_id=user1.id,
            activity_type="spot_created",
            target_type="spot",
            target_id="spot1",
        )

        retrieved = activity_repo.get_activity_by_id(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.user_id == user1.id

    def test_get_activity_by_id_not_found(self, activity_repo: ActivityRepository):
        """Test getting a non-existent activity."""
        activity = activity_repo.get_activity_by_id("nonexistent")

        assert activity is None

    def test_get_activities_for_target(
        self, activity_repo: ActivityRepository, users: tuple[UserORM, UserORM, UserORM]
    ):
        """Test getting all activities for a specific target."""
        user1, user2, _ = users

        activity_repo.create_activity(user1.id, "spot_rated", "rating", "spot1_rating")
        activity_repo.create_activity(user2.id, "spot_commented", "comment", "spot1_comment")
        activity_repo.create_activity(user1.id, "spot_favorited", "favorite", "spot2_fav")

        # Get all activities for spot1_rating target
        activities = activity_repo.get_activities_for_target("rating", "spot1_rating")

        assert len(activities) == 1
        assert activities[0].target_id == "spot1_rating"

    def test_pagination(
        self, activity_repo: ActivityRepository, users: tuple[UserORM, UserORM, UserORM]
    ):
        """Test pagination in feed queries."""
        user1, _, _ = users

        # Create 30 activities
        for i in range(30):
            activity_repo.create_activity(user1.id, "spot_created", "spot", f"spot{i}")

        # Get first page
        activities1, total1 = activity_repo.get_public_feed(limit=10, offset=0)
        assert len(activities1) == 10
        assert total1 == 30

        # Get second page
        activities2, total2 = activity_repo.get_public_feed(limit=10, offset=10)
        assert len(activities2) == 10
        assert total2 == 30

        # Verify different activities
        ids1 = {a.id for a in activities1}
        ids2 = {a.id for a in activities2}
        assert ids1.isdisjoint(ids2)
