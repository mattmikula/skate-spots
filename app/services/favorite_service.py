"""Service layer for managing user favorite skate spots."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any
from uuid import UUID  # noqa: TCH003

from fastapi import Depends

from app.core.dependencies import get_db
from app.core.logging import get_logger
from app.models.favorite import FavoriteStatus
from app.models.skate_spot import SkateSpot  # noqa: TCH001
from app.repositories.favorite_repository import FavoriteRepository
from app.repositories.skate_spot_repository import SkateSpotRepository

if TYPE_CHECKING:
    from app.services.activity_service import ActivityService


class FavoriteService:
    """Business logic for favorite skate spots."""

    def __init__(
        self,
        favorite_repository: FavoriteRepository,
        skate_spot_repository: SkateSpotRepository,
        activity_service: ActivityService | None = None,
    ) -> None:
        self._favorite_repository = favorite_repository
        self._skate_spot_repository = skate_spot_repository
        self._activity_service = activity_service
        self._logger = get_logger(__name__)

    def add_favorite(self, spot_id: UUID, user_id: str) -> FavoriteStatus:
        """Ensure the spot is marked as a favorite for the user."""

        self._ensure_spot_exists(spot_id)
        if not self._favorite_repository.exists(user_id, spot_id):
            self._favorite_repository.add(user_id, spot_id)
            self._logger.info("favorite added", spot_id=str(spot_id), user_id=user_id)

            # Record activity
            if self._activity_service:
                try:
                    self._activity_service.record_spot_favorited(user_id, str(spot_id))
                except Exception as e:
                    self._logger.warning("failed to record favorite activity", error=str(e))
        else:
            self._logger.debug("favorite already exists", spot_id=str(spot_id), user_id=user_id)
        return FavoriteStatus(spot_id=spot_id, is_favorite=True)

    def remove_favorite(self, spot_id: UUID, user_id: str) -> FavoriteStatus:
        """Remove the spot from the user's favorites."""

        self._ensure_spot_exists(spot_id)
        removed = self._favorite_repository.remove(user_id, spot_id)
        if removed:
            self._logger.info("favorite removed", spot_id=str(spot_id), user_id=user_id)
        else:
            self._logger.debug(
                "favorite removal requested for missing record",
                spot_id=str(spot_id),
                user_id=user_id,
            )
        return FavoriteStatus(spot_id=spot_id, is_favorite=False)

    def toggle_favorite(self, spot_id: UUID, user_id: str) -> FavoriteStatus:
        """Toggle favorite status for the given user and skate spot."""

        self._ensure_spot_exists(spot_id)
        if self._favorite_repository.exists(user_id, spot_id):
            return self.remove_favorite(spot_id, user_id)
        return self.add_favorite(spot_id, user_id)

    def list_user_favorites(self, user_id: str) -> list[SkateSpot]:
        """Return the favorite skate spots for the specified user."""

        spot_ids = self._favorite_repository.list_spot_ids_for_user(user_id)
        if not spot_ids:
            return []
        spots = self._skate_spot_repository.get_many_by_ids(spot_ids)
        self._logger.debug(
            "favorite spots listed",
            user_id=user_id,
            count=len(spots),
        )
        return spots

    def favorite_ids_for_user(self, user_id: str) -> set[UUID]:
        """Return a set of spot identifiers favorited by the user."""

        return set(self._favorite_repository.list_spot_ids_for_user(user_id))

    def _ensure_spot_exists(self, spot_id: UUID) -> SkateSpot:
        """Raise when the requested spot cannot be found."""

        spot = self._skate_spot_repository.get_by_id(spot_id)
        if spot is None:
            self._logger.warning("favorite requested for missing spot", spot_id=str(spot_id))
            raise SpotNotFoundError(f"Skate spot with id {spot_id} not found.")
        return spot


class SpotNotFoundError(Exception):
    """Raised when a skate spot cannot be found."""


def get_favorite_service(
    db: Annotated[Any, Depends(get_db)],
) -> FavoriteService:
    """FastAPI dependency hook to create favorite service with activity tracking.

    Args:
        db: Database session from dependency injection

    Returns:
        FavoriteService instance with repositories initialized
    """
    from app.services.activity_service import get_activity_service

    favorite_repository = FavoriteRepository()
    skate_spot_repository = SkateSpotRepository()
    activity_service = get_activity_service(db)
    return FavoriteService(favorite_repository, skate_spot_repository, activity_service)
