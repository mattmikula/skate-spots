"""Service layer for skate spot operations backed by SQLite."""

from __future__ import annotations

from typing import TYPE_CHECKING

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


class SkateSpotService:
    """Service class for skate spot business logic."""

    def __init__(self, repository: SkateSpotRepository) -> None:
        self._repository = repository
        self._logger = get_logger(__name__)

    def create_spot(self, spot_data: SkateSpotCreate, user_id: str) -> SkateSpot:
        """Create a new skate spot with validation."""

        spot = self._repository.create(spot_data, user_id)
        self._logger.info("skate spot created", spot_id=str(spot.id), owner_id=user_id)
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


_repository = SkateSpotRepository()
skate_spot_service = SkateSpotService(_repository)


def get_skate_spot_service() -> SkateSpotService:
    """Provide the default skate spot service for dependency injection."""

    return skate_spot_service
