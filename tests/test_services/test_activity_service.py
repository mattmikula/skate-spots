"""Tests for the activity service."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from app.db.models import UserFollowORM, UserORM
from app.services.activity_service import ActivityService

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


@pytest.fixture
def activity_service(db: Session) -> ActivityService:
    """Create an activity service instance."""
    return ActivityService(db)


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


class TestActivityService:
    """Test cases for ActivityService."""

    def test_record_spot_created(
        self, activity_service: ActivityService, users: tuple[UserORM, UserORM, UserORM]
    ):
        """Test recording spot creation activity."""
        user1, _, _ = users

        activity = activity_service.record_spot_created(user1.id, "spot123", "Test Spot")

        assert activity is not None
        assert activity.user_id == user1.id
        assert activity.activity_type == "spot_created"
        assert activity.target_type == "spot"
        assert activity.target_id == "spot123"

    def test_record_spot_rated(
        self, activity_service: ActivityService, users: tuple[UserORM, UserORM, UserORM]
    ):
        """Test recording spot rating activity."""
        user1, _, _ = users

        activity = activity_service.record_spot_rated(user1.id, "spot123", "rating456", 5)

        assert activity is not None
        assert activity.user_id == user1.id
        assert activity.activity_type == "spot_rated"
        assert activity.target_type == "rating"

    def test_record_spot_commented(
        self, activity_service: ActivityService, users: tuple[UserORM, UserORM, UserORM]
    ):
        """Test recording comment activity."""
        user1, _, _ = users

        activity = activity_service.record_spot_commented(user1.id, "spot123", "comment789")

        assert activity is not None
        assert activity.user_id == user1.id
        assert activity.activity_type == "spot_commented"
        assert activity.target_type == "comment"

    def test_record_spot_favorited(
        self, activity_service: ActivityService, users: tuple[UserORM, UserORM, UserORM]
    ):
        """Test recording favorite activity."""
        user1, _, _ = users

        activity = activity_service.record_spot_favorited(user1.id, "spot123")

        assert activity is not None
        assert activity.user_id == user1.id
        assert activity.activity_type == "spot_favorited"
        assert activity.target_type == "favorite"

    def test_record_session_created(
        self, activity_service: ActivityService, users: tuple[UserORM, UserORM, UserORM]
    ):
        """Test recording session creation activity."""
        user1, _, _ = users

        activity = activity_service.record_session_created(user1.id, "session111", "Skate Session")

        assert activity is not None
        assert activity.user_id == user1.id
        assert activity.activity_type == "session_created"
        assert activity.target_type == "session"

    def test_record_session_rsvp(
        self, activity_service: ActivityService, users: tuple[UserORM, UserORM, UserORM]
    ):
        """Test recording session RSVP activity."""
        user1, _, _ = users

        activity = activity_service.record_session_rsvp(user1.id, "session111", "rsvp222", "going")

        assert activity is not None
        assert activity.user_id == user1.id
        assert activity.activity_type == "session_rsvp"
        assert activity.target_type == "rsvp"

    def test_get_personalized_feed_empty(
        self, activity_service: ActivityService, users: tuple[UserORM, UserORM, UserORM]
    ):
        """Test getting empty personalized feed."""
        user1, _, _ = users

        feed = activity_service.get_personalized_feed(user1.id)

        assert feed.total == 0
        assert len(feed.activities) == 0
        assert feed.has_more is False

    def test_get_personalized_feed_with_follows(
        self,
        db: Session,
        activity_service: ActivityService,
        users: tuple[UserORM, UserORM, UserORM],
    ):
        """Test getting personalized feed from followed users."""
        user1, user2, user3 = users

        # user1 follows user2
        follow = UserFollowORM(follower_id=user1.id, following_id=user2.id)
        db.add(follow)
        db.commit()

        # Create activities
        activity_service.record_spot_created(user2.id, "spot1", "Spot 1")
        activity_service.record_spot_rated(user3.id, "spot2", "rating1", 4)  # Not followed

        feed = activity_service.get_personalized_feed(user1.id)

        assert feed.total == 1
        assert len(feed.activities) == 1
        assert feed.activities[0].actor.username == "user2"

    def test_get_public_feed(
        self, activity_service: ActivityService, users: tuple[UserORM, UserORM, UserORM]
    ):
        """Test getting public feed."""
        user1, user2, user3 = users

        activity_service.record_spot_created(user1.id, "spot1", "Spot 1")
        activity_service.record_spot_rated(user2.id, "spot2", "rating1", 5)
        activity_service.record_spot_commented(user3.id, "spot3", "comment1")

        feed = activity_service.get_public_feed()

        assert feed.total == 3
        assert len(feed.activities) == 3

    def test_get_user_activity(
        self, activity_service: ActivityService, users: tuple[UserORM, UserORM, UserORM]
    ):
        """Test getting activity history for a user."""
        user1, user2, _ = users

        activity_service.record_spot_created(user1.id, "spot1", "Spot 1")
        activity_service.record_spot_rated(user1.id, "spot2", "rating1", 4)
        activity_service.record_spot_created(user2.id, "spot3", "Spot 3")

        feed = activity_service.get_user_activity(user1.id)

        assert feed.total == 2
        assert len(feed.activities) == 2
        assert all(a.user_id == user1.id for a in feed.activities)

    def test_delete_activities_for_target(
        self, activity_service: ActivityService, users: tuple[UserORM, UserORM, UserORM]
    ):
        """Test deleting activities for a target."""
        user1, user2, _ = users

        activity_service.record_spot_created(user1.id, "spot1", "Spot 1")
        activity_service.record_spot_rated(user2.id, "spot1", "rating1", 5)

        deleted = activity_service.delete_activities_for_target("spot", "spot1")

        assert deleted == 1

        feed = activity_service.get_public_feed()
        assert feed.total == 1

    def test_pagination(
        self, activity_service: ActivityService, users: tuple[UserORM, UserORM, UserORM]
    ):
        """Test pagination in feeds."""
        user1, _, _ = users

        # Create multiple activities
        for i in range(25):
            activity_service.record_spot_created(user1.id, f"spot{i}", f"Spot {i}")

        # Get first page
        feed1 = activity_service.get_public_feed(limit=10, offset=0)
        assert len(feed1.activities) == 10
        assert feed1.has_more is True

        # Get second page
        feed2 = activity_service.get_public_feed(limit=10, offset=10)
        assert len(feed2.activities) == 10
        assert feed2.has_more is True

        # Get last page
        feed3 = activity_service.get_public_feed(limit=10, offset=20)
        assert len(feed3.activities) == 5
        assert feed3.has_more is False

    def test_activity_enrichment(
        self, activity_service: ActivityService, users: tuple[UserORM, UserORM, UserORM]
    ):
        """Test that activities are enriched with user info."""
        user1, _, _ = users

        activity_service.record_spot_created(user1.id, "spot1", "Test Spot")
        feed = activity_service.get_public_feed()

        assert len(feed.activities) == 1
        activity = feed.activities[0]
        assert activity.actor is not None
        assert activity.actor.username == user1.username
        assert str(activity.actor.id) == user1.id
