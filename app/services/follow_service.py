"""Service for managing user follow relationships."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import Depends

from app.core.dependencies import get_db
from app.models.follow import FollowerUser, FollowStats
from app.repositories.follow_repository import FollowRepository
from app.repositories.user_repository import UserRepository


class UserNotFoundError(Exception):
    """Exception raised when a user is not found."""

    pass


class FollowError(Exception):
    """Base exception for follow-related errors."""

    pass


class SelfFollowError(FollowError):
    """Exception raised when user tries to follow themselves."""

    pass


class AlreadyFollowingError(FollowError):
    """Exception raised when user is already following."""

    pass


class NotFollowingError(FollowError):
    """Exception raised when user is not following."""

    pass


class FollowService:
    """Service for managing user follow relationships."""

    def __init__(self, db: Any) -> None:
        """Initialize service with database session."""
        self.db = db
        self.follow_repository = FollowRepository(db)
        self.user_repository = UserRepository(db)

    def follow_user(self, follower_id: str, following_username: str) -> dict:
        """Follow a user.

        Args:
            follower_id: ID of the user doing the following
            following_username: Username of the user to follow

        Returns:
            Dictionary with follow information

        Raises:
            UserNotFoundError: If the user to follow doesn't exist
            SelfFollowError: If trying to follow yourself
            AlreadyFollowingError: If already following the user
        """
        # Get the user to follow by username
        following_user = self.user_repository.get_by_username(following_username)
        if not following_user:
            raise UserNotFoundError(f"User '{following_username}' not found")

        if follower_id == following_user.id:
            raise SelfFollowError("You cannot follow yourself")

        try:
            self.follow_repository.follow_user(follower_id, following_user.id)
            return {
                "status": "following",
                "user_id": following_user.id,
                "username": following_user.username,
            }
        except ValueError as exc:
            if "already following" in str(exc).lower():
                raise AlreadyFollowingError(f"Already following {following_username}") from exc
            raise FollowError(str(exc)) from exc

    def unfollow_user(self, follower_id: str, following_username: str) -> bool:
        """Unfollow a user.

        Args:
            follower_id: ID of the user doing the unfollowing
            following_username: Username of the user to unfollow

        Returns:
            True if successfully unfollowed

        Raises:
            UserNotFoundError: If the user doesn't exist
            NotFollowingError: If not currently following the user
        """
        following_user = self.user_repository.get_by_username(following_username)
        if not following_user:
            raise UserNotFoundError(f"User '{following_username}' not found")

        success = self.follow_repository.unfollow_user(follower_id, following_user.id)
        if not success:
            raise NotFollowingError(f"Not following {following_username}")

        return True

    def is_following(self, follower_id: str, following_username: str) -> bool:
        """Check if user is following another user.

        Args:
            follower_id: ID of the potential follower
            following_username: Username of the user to check

        Returns:
            True if follower_id is following following_username

        Raises:
            UserNotFoundError: If the user doesn't exist
        """
        following_user = self.user_repository.get_by_username(following_username)
        if not following_user:
            raise UserNotFoundError(f"User '{following_username}' not found")

        return self.follow_repository.is_following(follower_id, following_user.id)

    def get_followers(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> tuple[list[FollowerUser], int]:
        """Get followers of a user.

        Args:
            user_id: ID of the user
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            Tuple of (list of follower users, total count)
        """
        followers, total = self.follow_repository.get_followers(user_id, limit, offset)
        follower_models = [
            FollowerUser(
                id=f.id,
                username=f.username,
                display_name=f.display_name,
                profile_photo_url=f.profile_photo_url,
            )
            for f in followers
        ]
        return follower_models, total

    def get_following(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> tuple[list[FollowerUser], int]:
        """Get users that a user is following.

        Args:
            user_id: ID of the user
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            Tuple of (list of users being followed, total count)
        """
        following, total = self.follow_repository.get_following(user_id, limit, offset)
        following_models = [
            FollowerUser(
                id=f.id,
                username=f.username,
                display_name=f.display_name,
                profile_photo_url=f.profile_photo_url,
            )
            for f in following
        ]
        return following_models, total

    def get_follow_stats(self, user_id: str) -> FollowStats:
        """Get follower and following statistics for a user.

        Args:
            user_id: ID of the user

        Returns:
            FollowStats model with counts
        """
        return self.follow_repository.get_follow_stats(user_id)


def get_follow_service(db: Annotated[Any, Depends(get_db)]) -> FollowService:
    """Get follow service dependency.

    Args:
        db: Database session

    Returns:
        FollowService instance
    """
    return FollowService(db)
