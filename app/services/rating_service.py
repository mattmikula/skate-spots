"""Service layer for skate spot rating operations."""

from __future__ import annotations

import uuid  # noqa: TC003
from typing import TYPE_CHECKING

from app.core.logging import get_logger
from app.models.rating import Rating, RatingCreate, RatingSummaryResponse
from app.repositories.rating_repository import RatingRepository
from app.repositories.skate_spot_repository import SkateSpotRepository

if TYPE_CHECKING:
    from app.models.skate_spot import SkateSpot


class SpotNotFoundError(Exception):
    """Raised when the requested skate spot does not exist."""


class RatingNotFoundError(Exception):
    """Raised when a rating does not exist for the given user and spot."""


class RatingService:
    """Business logic for managing skate spot ratings."""

    def __init__(
        self,
        rating_repository: RatingRepository,
        skate_spot_repository: SkateSpotRepository,
    ) -> None:
        self._rating_repository = rating_repository
        self._skate_spot_repository = skate_spot_repository
        self._logger = get_logger(__name__)

    def _ensure_spot_exists(self, spot_id: uuid.UUID) -> SkateSpot:
        spot = self._skate_spot_repository.get_by_id(spot_id)
        if spot is None:
            self._logger.warning("rating requested for missing spot", spot_id=str(spot_id))
            raise SpotNotFoundError(f"Skate spot with id {spot_id} not found.")
        return spot

    def set_rating(
        self, spot_id: uuid.UUID, user_id: str, rating_data: RatingCreate
    ) -> RatingSummaryResponse:
        """Create or update a user's rating for a given spot."""

        self._ensure_spot_exists(spot_id)
        rating = self._rating_repository.upsert(spot_id, user_id, rating_data)
        summary = self._rating_repository.get_summary(spot_id)
        self._logger.info(
            "rating set",
            spot_id=str(spot_id),
            user_id=user_id,
            score=rating.score,
        )
        return RatingSummaryResponse(**summary.model_dump(), user_rating=rating)

    def get_user_rating(self, spot_id: uuid.UUID, user_id: str) -> Rating:
        """Return the rating created by the user for the given spot."""

        self._ensure_spot_exists(spot_id)
        rating = self._rating_repository.get_user_rating(spot_id, user_id)
        if rating is None:
            self._logger.debug(
                "user rating not found",
                spot_id=str(spot_id),
                user_id=user_id,
            )
            raise RatingNotFoundError("Rating not found for this user and skate spot.")
        return rating

    def delete_rating(self, spot_id: uuid.UUID, user_id: str) -> RatingSummaryResponse:
        """Remove the user's rating for the given spot."""

        self._ensure_spot_exists(spot_id)
        deleted = self._rating_repository.delete_rating(spot_id, user_id)
        if not deleted:
            self._logger.debug(
                "delete requested for missing rating",
                spot_id=str(spot_id),
                user_id=user_id,
            )
            raise RatingNotFoundError("Rating not found for this user and skate spot.")

        summary = self._rating_repository.get_summary(spot_id)
        self._logger.info("rating deleted", spot_id=str(spot_id), user_id=user_id)
        return RatingSummaryResponse(**summary.model_dump(), user_rating=None)

    def get_summary(self, spot_id: uuid.UUID, user_id: str | None = None) -> RatingSummaryResponse:
        """Return rating summary for a spot, optionally including the user's rating."""

        self._ensure_spot_exists(spot_id)
        summary = self._rating_repository.get_summary(spot_id)
        user_rating = None
        if user_id is not None:
            user_rating = self._rating_repository.get_user_rating(spot_id, user_id)

        return RatingSummaryResponse(**summary.model_dump(), user_rating=user_rating)


_rating_repository = RatingRepository()
_skate_spot_repository = SkateSpotRepository()
rating_service = RatingService(_rating_repository, _skate_spot_repository)


def get_rating_service() -> RatingService:
    """FastAPI dependency hook for obtaining the rating service."""

    return rating_service
