"""Service layer for ratings business logic."""

from uuid import UUID

from app.models.rating import Rating, RatingCreate, RatingStats, RatingUpdate
from app.repositories.rating_repository import RatingRepository


class RatingService:
    """Service handling business logic for ratings."""

    def __init__(self, repository: RatingRepository) -> None:
        self._repository = repository

    def create_rating(self, spot_id: UUID, user_id: str, rating_data: RatingCreate) -> Rating:
        """Create a new rating for a skate spot."""
        return self._repository.create(rating_data, spot_id, user_id)

    def get_rating(self, rating_id: UUID) -> Rating | None:
        """Get a rating by ID."""
        return self._repository.get_by_id(rating_id)

    def get_user_rating_for_spot(self, spot_id: UUID, user_id: str) -> Rating | None:
        """Get a specific user's rating for a spot."""
        return self._repository.get_by_spot_and_user(spot_id, user_id)

    def get_spot_ratings(self, spot_id: UUID) -> list[Rating]:
        """Get all ratings for a spot."""
        return self._repository.get_by_spot(spot_id)

    def get_spot_rating_stats(self, spot_id: UUID) -> RatingStats:
        """Get rating statistics for a spot."""
        return self._repository.get_stats_for_spot(spot_id)

    def update_rating(self, rating_id: UUID, update_data: RatingUpdate) -> Rating | None:
        """Update an existing rating."""
        return self._repository.update(rating_id, update_data)

    def delete_rating(self, rating_id: UUID) -> bool:
        """Delete a rating."""
        return self._repository.delete(rating_id)

    def is_owner(self, rating_id: UUID, user_id: str) -> bool:
        """Check if a user owns a rating."""
        return self._repository.is_owner(rating_id, user_id)


def get_rating_service() -> RatingService:
    """Dependency injection for RatingService."""
    return RatingService(RatingRepository())
