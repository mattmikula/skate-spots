"""Tests for the follow service."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from app.db.models import UserORM
from app.services.follow_service import (
    AlreadyFollowingError,
    FollowService,
    NotFollowingError,
    SelfFollowError,
    UserNotFoundError,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


@pytest.fixture
def follow_service(db: Session) -> FollowService:
    """Create a follow service instance."""
    return FollowService(db)


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


class TestFollowService:
    """Test cases for FollowService."""

    def test_follow_user_success(
        self, follow_service: FollowService, users: tuple[UserORM, UserORM, UserORM]
    ):
        """Test successfully following a user."""
        user1, user2, _ = users

        result = follow_service.follow_user(user1.id, user2.username)

        assert result["status"] == "following"
        assert result["user_id"] == user2.id
        assert result["username"] == user2.username

    def test_follow_user_not_found(
        self, follow_service: FollowService, users: tuple[UserORM, UserORM, UserORM]
    ):
        """Test following a non-existent user."""
        user1, _, _ = users

        with pytest.raises(UserNotFoundError):
            follow_service.follow_user(user1.id, "nonexistent")

    def test_follow_user_self(
        self, follow_service: FollowService, users: tuple[UserORM, UserORM, UserORM]
    ):
        """Test that users can't follow themselves."""
        user1, _, _ = users

        with pytest.raises(SelfFollowError):
            follow_service.follow_user(user1.id, user1.username)

    def test_follow_user_already_following(
        self, follow_service: FollowService, users: tuple[UserORM, UserORM, UserORM]
    ):
        """Test that following twice raises an error."""
        user1, user2, _ = users

        follow_service.follow_user(user1.id, user2.username)

        with pytest.raises(AlreadyFollowingError):
            follow_service.follow_user(user1.id, user2.username)

    def test_unfollow_user_success(
        self, follow_service: FollowService, users: tuple[UserORM, UserORM, UserORM]
    ):
        """Test successfully unfollowing a user."""
        user1, user2, _ = users

        follow_service.follow_user(user1.id, user2.username)
        result = follow_service.unfollow_user(user1.id, user2.username)

        assert result is True

    def test_unfollow_user_not_found(
        self, follow_service: FollowService, users: tuple[UserORM, UserORM, UserORM]
    ):
        """Test unfollowing a non-existent user."""
        user1, _, _ = users

        with pytest.raises(UserNotFoundError):
            follow_service.unfollow_user(user1.id, "nonexistent")

    def test_unfollow_user_not_following(
        self, follow_service: FollowService, users: tuple[UserORM, UserORM, UserORM]
    ):
        """Test unfollowing a user you're not following."""
        user1, user2, _ = users

        with pytest.raises(NotFollowingError):
            follow_service.unfollow_user(user1.id, user2.username)

    def test_is_following_true(
        self, follow_service: FollowService, users: tuple[UserORM, UserORM, UserORM]
    ):
        """Test checking if following when user is followed."""
        user1, user2, _ = users

        follow_service.follow_user(user1.id, user2.username)
        result = follow_service.is_following(user1.id, user2.username)

        assert result is True

    def test_is_following_false(
        self, follow_service: FollowService, users: tuple[UserORM, UserORM, UserORM]
    ):
        """Test checking if following when user is not followed."""
        user1, user2, _ = users

        result = follow_service.is_following(user1.id, user2.username)

        assert result is False

    def test_is_following_user_not_found(
        self, follow_service: FollowService, users: tuple[UserORM, UserORM, UserORM]
    ):
        """Test checking follow status of non-existent user."""
        user1, _, _ = users

        with pytest.raises(UserNotFoundError):
            follow_service.is_following(user1.id, "nonexistent")

    def test_get_followers(
        self, follow_service: FollowService, users: tuple[UserORM, UserORM, UserORM]
    ):
        """Test getting followers of a user."""
        user1, user2, user3 = users

        follow_service.follow_user(user1.id, user2.username)
        follow_service.follow_user(user3.id, user2.username)

        followers, total = follow_service.get_followers(user2.id)

        assert total == 2
        assert len(followers) == 2
        assert any(f.username == user1.username for f in followers)
        assert any(f.username == user3.username for f in followers)

    def test_get_following(
        self, follow_service: FollowService, users: tuple[UserORM, UserORM, UserORM]
    ):
        """Test getting users that a user is following."""
        user1, user2, user3 = users

        follow_service.follow_user(user1.id, user2.username)
        follow_service.follow_user(user1.id, user3.username)

        following, total = follow_service.get_following(user1.id)

        assert total == 2
        assert len(following) == 2
        assert any(f.username == user2.username for f in following)
        assert any(f.username == user3.username for f in following)

    def test_get_follow_stats(
        self, follow_service: FollowService, users: tuple[UserORM, UserORM, UserORM]
    ):
        """Test getting follow statistics."""
        user1, user2, user3 = users

        follow_service.follow_user(user1.id, user2.username)
        follow_service.follow_user(user3.id, user2.username)
        follow_service.follow_user(user2.id, user1.username)

        stats = follow_service.get_follow_stats(user2.id)

        assert stats.followers_count == 2
        assert stats.following_count == 1
