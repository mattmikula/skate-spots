"""Tests for the follow repository."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from app.db.models import UserORM
from app.repositories.follow_repository import FollowRepository

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


@pytest.fixture
def follow_repo(db: Session) -> FollowRepository:
    """Create a follow repository instance."""
    return FollowRepository(db)


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


class TestFollowRepository:
    """Test cases for FollowRepository."""

    def test_follow_user_success(
        self, follow_repo: FollowRepository, users: tuple[UserORM, UserORM, UserORM]
    ):
        """Test successfully following a user."""
        user1, user2, _ = users
        follow = follow_repo.follow_user(user1.id, user2.id)

        assert follow is not None
        assert follow.follower_id == user1.id
        assert follow.following_id == user2.id

    def test_follow_user_self_raises_error(
        self, follow_repo: FollowRepository, users: tuple[UserORM, UserORM, UserORM]
    ):
        """Test that following yourself raises an error."""
        user1, _, _ = users

        with pytest.raises(ValueError, match="cannot follow themselves"):
            follow_repo.follow_user(user1.id, user1.id)

    def test_follow_user_duplicate_raises_error(
        self, follow_repo: FollowRepository, users: tuple[UserORM, UserORM, UserORM]
    ):
        """Test that following the same user twice raises an error."""
        user1, user2, _ = users

        follow_repo.follow_user(user1.id, user2.id)

        with pytest.raises(ValueError, match="Already following"):
            follow_repo.follow_user(user1.id, user2.id)

    def test_unfollow_user_success(
        self, follow_repo: FollowRepository, users: tuple[UserORM, UserORM, UserORM]
    ):
        """Test successfully unfollowing a user."""
        user1, user2, _ = users

        follow_repo.follow_user(user1.id, user2.id)
        result = follow_repo.unfollow_user(user1.id, user2.id)

        assert result is True

    def test_unfollow_user_not_following(
        self, follow_repo: FollowRepository, users: tuple[UserORM, UserORM, UserORM]
    ):
        """Test unfollowing a user you're not following."""
        user1, user2, _ = users

        result = follow_repo.unfollow_user(user1.id, user2.id)

        assert result is False

    def test_is_following_true(
        self, follow_repo: FollowRepository, users: tuple[UserORM, UserORM, UserORM]
    ):
        """Test checking if following when user is followed."""
        user1, user2, _ = users

        follow_repo.follow_user(user1.id, user2.id)
        result = follow_repo.is_following(user1.id, user2.id)

        assert result is True

    def test_is_following_false(
        self, follow_repo: FollowRepository, users: tuple[UserORM, UserORM, UserORM]
    ):
        """Test checking if following when user is not followed."""
        user1, user2, _ = users

        result = follow_repo.is_following(user1.id, user2.id)

        assert result is False

    def test_get_followers(
        self, follow_repo: FollowRepository, users: tuple[UserORM, UserORM, UserORM]
    ):
        """Test getting followers of a user."""
        user1, user2, user3 = users

        # user1 and user3 follow user2
        follow_repo.follow_user(user1.id, user2.id)
        follow_repo.follow_user(user3.id, user2.id)

        followers, total = follow_repo.get_followers(user2.id)

        assert total == 2
        assert len(followers) == 2
        assert any(f.id == user1.id for f in followers)
        assert any(f.id == user3.id for f in followers)

    def test_get_following(
        self, follow_repo: FollowRepository, users: tuple[UserORM, UserORM, UserORM]
    ):
        """Test getting users that a user is following."""
        user1, user2, user3 = users

        # user1 follows user2 and user3
        follow_repo.follow_user(user1.id, user2.id)
        follow_repo.follow_user(user1.id, user3.id)

        following, total = follow_repo.get_following(user1.id)

        assert total == 2
        assert len(following) == 2
        assert any(f.id == user2.id for f in following)
        assert any(f.id == user3.id for f in following)

    def test_get_follow_stats(
        self, follow_repo: FollowRepository, users: tuple[UserORM, UserORM, UserORM]
    ):
        """Test getting follow statistics."""
        user1, user2, user3 = users

        # user1 follows user2
        # user3 follows user2
        # user2 follows user1
        follow_repo.follow_user(user1.id, user2.id)
        follow_repo.follow_user(user3.id, user2.id)
        follow_repo.follow_user(user2.id, user1.id)

        stats_user2 = follow_repo.get_follow_stats(user2.id)

        assert stats_user2["followers_count"] == 2
        assert stats_user2["following_count"] == 1

    def test_get_followers_pagination(
        self, follow_repo: FollowRepository, users: tuple[UserORM, UserORM, UserORM]
    ):
        """Test pagination in get_followers."""
        user1, user2, user3 = users

        follow_repo.follow_user(user1.id, user2.id)
        follow_repo.follow_user(user3.id, user2.id)

        # Get only first result
        followers, total = follow_repo.get_followers(user2.id, limit=1, offset=0)

        assert total == 2
        assert len(followers) == 1
