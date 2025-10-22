"""Service layer for skate spot operations backed by SQLite."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any

from fastapi import Depends

from app.core.dependencies import get_db
from app.core.logging import get_logger
from app.repositories.skate_spot_repository import SkateSpotRepository
from app.services.photo_storage import delete_photos

if TYPE_CHECKING:
    from uuid import UUID

    from app.models.skate_spot import (
        SkateSpot,
        SkateSpotCreate,
        SkateSpotFilters,
        SkateSpotUpdate,
    )
    from app.services.activity_service import ActivityService


class SkateSpotService:
    """Service class for skate spot business logic."""

    def __init__(
        self, repository: SkateSpotRepository, activity_service: ActivityService | None = None
    ) -> None:
        self._repository = repository
        self._activity_service = activity_service
        self._logger = get_logger(__name__)

    def create_spot(self, spot_data: SkateSpotCreate, user_id: str) -> SkateSpot:
        """Create a new skate spot with validation."""

        spot = self._repository.create(spot_data, user_id)
        self._logger.info("skate spot created", spot_id=str(spot.id), owner_id=user_id)

        # Record activity
        if self._activity_service:
            try:
                self._activity_service.record_spot_created(user_id, str(spot.id), spot.name)
            except Exception as e:
                self._logger.warning("failed to record spot creation activity", error=str(e))

        return spot

    def get_spot(self, spot_id: UUID) -> SkateSpot | None:
        """Get a skate spot by ID."""

        spot = self._repository.get_by_id(spot_id)
        if spot is None:
            self._logger.warning("skate spot not found", spot_id=str(spot_id))
        return spot

    def list_spots(self, filters: SkateSpotFilters | None = None) -> list[SkateSpot]:
        """Get all skate spots with optional filtering."""

        spots = self._repository.get_all(filters)
        self._logger.debug("listed skate spots", count=len(spots))
        return spots

    def update_spot(self, spot_id: UUID, update_data: SkateSpotUpdate) -> SkateSpot | None:
        """Update an existing skate spot."""

        spot = self._repository.update(spot_id, update_data)
        if spot is None:
            self._logger.warning("failed to update missing skate spot", spot_id=str(spot_id))
            return None
        self._logger.info("skate spot updated", spot_id=str(spot.id))
        return spot

    def delete_spot(self, spot_id: UUID) -> bool:
        """Delete a skate spot by ID."""

        existing = self._repository.get_by_id(spot_id)
        deleted = self._repository.delete(spot_id)
        if deleted:
            self._logger.info("skate spot deleted", spot_id=str(spot_id))
            if existing and existing.photos:
                delete_photos(photo.path for photo in existing.photos)
        else:
            self._logger.warning("delete requested for missing skate spot", spot_id=str(spot_id))
        return deleted

    def is_owner(self, spot_id: UUID, user_id: str) -> bool:
        """Check if a user owns a skate spot."""

        is_owner = self._repository.is_owner(spot_id, user_id)
        self._logger.debug(
            "ownership check", spot_id=str(spot_id), user_id=user_id, is_owner=is_owner
        )
        return is_owner


def get_skate_spot_service(db: Annotated[Any, Depends(get_db)]) -> SkateSpotService:
    """Provide the skate spot service with activity tracking for dependency injection.

    Args:
        db: Database session from dependency injection

    Returns:
        SkateSpotService instance with activity service
    """
    from app.services.activity_service import get_activity_service

    repository = SkateSpotRepository(db)
    activity_service = get_activity_service(db)
    return SkateSpotService(repository, activity_service)
