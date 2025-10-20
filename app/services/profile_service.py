"""Business logic for user profiles."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.logging import get_logger
from app.models.profile import PublicUserInfo, UserActivity, UserProfile
from app.repositories.profile_repository import ProfileRepository

if TYPE_CHECKING:  # pragma: no cover - for type checking only
    from uuid import UUID


class UserNotFoundError(Exception):
    """Raised when a user cannot be located."""


class ProfileService:
    """Coordinate user profile data retrieval and presentation."""

    def __init__(self, profile_repository: ProfileRepository) -> None:
        self._profile_repository = profile_repository
        self._logger = get_logger(__name__)

    def get_profile_by_username(
        self,
        username: str,
        recent_spots_limit: int = 5,
        recent_comments_limit: int = 5,
        recent_ratings_limit: int = 5,
        activity_limit: int = 10,
    ) -> UserProfile:
        """Get a complete user profile by username."""
        user = self._profile_repository.get_user_by_username(username)
        if user is None:
            self._logger.warning("profile requested for missing user", username=username)
            raise UserNotFoundError(f"User '{username}' not found.")

        return self._get_profile_for_user(
            user_id=user.id,
            recent_spots_limit=recent_spots_limit,
            recent_comments_limit=recent_comments_limit,
            recent_ratings_limit=recent_ratings_limit,
            activity_limit=activity_limit,
        )

    def get_profile_by_id(
        self,
        user_id: UUID | str,
        recent_spots_limit: int = 5,
        recent_comments_limit: int = 5,
        recent_ratings_limit: int = 5,
        activity_limit: int = 10,
    ) -> UserProfile:
        """Get a complete user profile by user ID."""
        user = self._profile_repository.get_user_by_id(user_id)
        if user is None:
            self._logger.warning("profile requested for missing user", user_id=str(user_id))
            raise UserNotFoundError(f"User with id {user_id} not found.")

        return self._get_profile_for_user(
            user_id=user.id,
            recent_spots_limit=recent_spots_limit,
            recent_comments_limit=recent_comments_limit,
            recent_ratings_limit=recent_ratings_limit,
            activity_limit=activity_limit,
        )

    def _get_profile_for_user(
        self,
        user_id: UUID | str,
        recent_spots_limit: int,
        recent_comments_limit: int,
        recent_ratings_limit: int,
        activity_limit: int,
    ) -> UserProfile:
        """Internal method to build a complete user profile."""
        user = self._profile_repository.get_user_by_id(user_id)

        # Gather all profile data
        statistics = self._profile_repository.get_user_statistics(user_id)
        recent_spots = self._profile_repository.get_recent_spots(user_id, limit=recent_spots_limit)
        recent_comments = self._profile_repository.get_recent_comments(
            user_id, limit=recent_comments_limit
        )
        recent_ratings = self._profile_repository.get_recent_ratings(
            user_id, limit=recent_ratings_limit
        )
        activities = self._profile_repository.get_user_activity(user_id, limit=activity_limit)

        self._logger.info(
            "profile retrieved",
            user_id=str(user_id),
            username=user.username,
            spots=len(recent_spots),
            comments=len(recent_comments),
            ratings=len(recent_ratings),
            activities=len(activities),
        )

        return UserProfile(
            user=PublicUserInfo(
                id=user.id,
                username=user.username,
                created_at=user.created_at,
            ),
            statistics=statistics,
            recent_spots=recent_spots,
            recent_comments=recent_comments,
            recent_ratings=recent_ratings,
            activity=UserActivity(activities=activities),
        )


_profile_repository = ProfileRepository()
_profile_service = ProfileService(_profile_repository)


def get_profile_service() -> ProfileService:
    """FastAPI dependency hook for the shared profile service."""
    return _profile_service
