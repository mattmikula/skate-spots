"""Service layer for skate spot operations backed by SQLite."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.repositories.skate_spot_repository import SkateSpotRepository

if TYPE_CHECKING:
    from uuid import UUID

    from app.models.skate_spot import SkateSpot, SkateSpotCreate, SkateSpotUpdate


class SkateSpotService:
    """Service class for skate spot business logic."""

    def __init__(self, repository: SkateSpotRepository) -> None:
        self._repository = repository

    def create_spot(self, spot_data: SkateSpotCreate, user_id: str) -> SkateSpot:
        """Create a new skate spot with validation."""

        return self._repository.create(spot_data, user_id)

    def get_spot(self, spot_id: UUID) -> SkateSpot | None:
        """Get a skate spot by ID."""

        return self._repository.get_by_id(spot_id)

    def list_spots(self) -> list[SkateSpot]:
        """Get all skate spots."""

        return self._repository.get_all()

    def update_spot(self, spot_id: UUID, update_data: SkateSpotUpdate) -> SkateSpot | None:
        """Update an existing skate spot."""

        return self._repository.update(spot_id, update_data)

    def delete_spot(self, spot_id: UUID) -> bool:
        """Delete a skate spot by ID."""

        return self._repository.delete(spot_id)

    def is_owner(self, spot_id: UUID, user_id: str) -> bool:
        """Check if a user owns a skate spot."""

        return self._repository.is_owner(spot_id, user_id)


_repository = SkateSpotRepository()
skate_spot_service = SkateSpotService(_repository)


def get_skate_spot_service() -> SkateSpotService:
    """Provide the default skate spot service for dependency injection."""

    return skate_spot_service
