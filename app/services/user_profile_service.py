"""Service layer for composing public user profile data."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.logging import get_logger
from app.repositories.user_profile_repository import UserProfileRepository

if TYPE_CHECKING:
    from app.models.user_profile import UserProfile


class UserProfileNotFoundError(Exception):
    """Raised when a requested user profile cannot be located."""


class UserProfileService:
    """Provide higher level access to public user profile data."""

    def __init__(self, repository: UserProfileRepository) -> None:
        self._repository = repository
        self._logger = get_logger(__name__)

    def get_profile(self, username: str) -> UserProfile:
        """Fetch a user's public profile, raising when missing."""

        profile = self._repository.get_by_username(username)
        if profile is None:
            self._logger.warning("user profile not found", username=username)
            raise UserProfileNotFoundError(f"User '{username}' not found")

        self._logger.debug("user profile retrieved", username=username)
        return profile


_repository = UserProfileRepository()
_service = UserProfileService(_repository)


def get_user_profile_service() -> UserProfileService:
    """FastAPI dependency for the user profile service."""

    return _service
