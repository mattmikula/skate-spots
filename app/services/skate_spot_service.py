"""Service layer for skate spot operations."""

from datetime import datetime
from uuid import UUID

from app.models.skate_spot import SkateSpot, SkateSpotCreate, SkateSpotUpdate


class SkateSpotRepository:
    """In-memory repository for skate spots."""

    def __init__(self) -> None:
        """Initialize empty repository."""
        self._spots: dict[UUID, SkateSpot] = {}

    def create(self, spot_data: SkateSpotCreate) -> SkateSpot:
        """Create a new skate spot."""
        spot = SkateSpot(**spot_data.model_dump())
        self._spots[spot.id] = spot
        return spot

    def get_by_id(self, spot_id: UUID) -> SkateSpot | None:
        """Get a skate spot by ID."""
        return self._spots.get(spot_id)

    def get_all(self) -> list[SkateSpot]:
        """Get all skate spots."""
        return list(self._spots.values())

    def update(self, spot_id: UUID, update_data: SkateSpotUpdate) -> SkateSpot | None:
        """Update an existing skate spot."""
        if spot_id not in self._spots:
            return None

        spot = self._spots[spot_id]
        update_dict = update_data.model_dump(exclude_unset=True)

        for field, value in update_dict.items():
            setattr(spot, field, value)

        spot.updated_at = datetime.utcnow()
        return spot

    def delete(self, spot_id: UUID) -> bool:
        """Delete a skate spot by ID."""
        if spot_id in self._spots:
            del self._spots[spot_id]
            return True
        return False


class SkateSpotService:
    """Service class for skate spot business logic."""

    def __init__(self, repository: SkateSpotRepository) -> None:
        """Initialize service with repository."""
        self._repository = repository

    def create_spot(self, spot_data: SkateSpotCreate) -> SkateSpot:
        """Create a new skate spot with validation."""
        return self._repository.create(spot_data)

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


# Global instance - in a real app, this would be injected via dependency injection
_repository = SkateSpotRepository()
skate_spot_service = SkateSpotService(_repository)
