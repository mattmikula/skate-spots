"""Service layer for managing spot check-ins."""

from __future__ import annotations

from uuid import UUID

from app.core.logging import get_logger
from app.models.checkin import Checkin, CheckinStats, CheckinSummary
from app.repositories.checkin_repository import CheckinRepository
from app.repositories.skate_spot_repository import SkateSpotRepository

logger = get_logger(__name__)


class CheckinAlreadyExistsError(Exception):
    """Raised when a user tries to check in twice on the same day."""

    ...


class CheckinNotFoundError(Exception):
    """Raised when a check-in is not found."""

    ...


class SpotNotFoundError(Exception):
    """Raised when a spot is not found."""

    ...


class CheckinService:
    """Business logic for spot check-ins."""

    def __init__(
        self,
        checkin_repository: CheckinRepository,
        spot_repository: SkateSpotRepository,
    ) -> None:
        self._checkin_repository = checkin_repository
        self._spot_repository = spot_repository
        self._logger = get_logger(__name__)

    def create_checkin(self, spot_id: UUID, user_id: str, notes: str | None = None) -> Checkin:
        """Create a new check-in, preventing duplicates on the same day."""

        spot_id_str = str(spot_id)

        # Verify spot exists
        if not self._spot_repository.get_by_id(spot_id):
            raise SpotNotFoundError(f"Spot {spot_id} not found")

        # Check for existing check-in today
        existing = self._checkin_repository.get_user_checkin_today(spot_id_str, user_id)
        if existing:
            raise CheckinAlreadyExistsError(
                f"User {user_id} already checked in to spot {spot_id} today"
            )

        # Create check-in
        orm_checkin = self._checkin_repository.create(spot_id_str, user_id, notes)
        self._logger.info("checkin created", spot_id=spot_id_str, user_id=user_id)

        return Checkin.model_validate(orm_checkin)

    def get_spot_stats(self, spot_id: UUID, user_id: str | None = None) -> CheckinStats:
        """Get aggregated check-in statistics for a spot."""

        spot_id_str = str(spot_id)
        stats_dict = self._checkin_repository.get_stats_for_spot(spot_id_str, user_id)

        return CheckinStats(**stats_dict)

    def get_user_history(self, user_id: str, limit: int = 50) -> list[CheckinSummary]:
        """Get user's check-in history."""

        orm_checkins = self._checkin_repository.list_for_user(user_id, limit)
        summaries = []

        for checkin in orm_checkins:
            # The spot relationship is eagerly loaded via selectinload in the repository
            spot_name = checkin.spot.name if checkin.spot else "Unknown Spot"
            summary = CheckinSummary(
                id=UUID(checkin.id),
                spot_id=UUID(checkin.spot_id),
                spot_name=spot_name,
                checked_in_at=checkin.checked_in_at,
                notes=checkin.notes,
            )
            summaries.append(summary)

        return summaries

    def get_spot_recent_checkins(self, spot_id: UUID, limit: int = 20) -> list[Checkin]:
        """Get recent check-ins for a spot."""

        spot_id_str = str(spot_id)
        orm_checkins = self._checkin_repository.list_for_spot(spot_id_str, limit)

        return [Checkin.model_validate(checkin) for checkin in orm_checkins]

    def delete_checkin(self, checkin_id: UUID, user_id: str, is_admin: bool = False) -> bool:
        """Delete a check-in with permission checks."""

        checkin_id_str = str(checkin_id)
        checkin = self._checkin_repository.get_by_id(checkin_id_str)

        if not checkin:
            raise CheckinNotFoundError(f"Check-in {checkin_id} not found")

        # Only the user who created it or admins can delete
        if checkin.user_id != user_id and not is_admin:
            raise PermissionError(
                f"User {user_id} does not have permission to delete check-in {checkin_id}"
            )

        success = self._checkin_repository.delete(checkin_id_str)
        if success:
            self._logger.info(
                "checkin deleted",
                checkin_id=checkin_id_str,
                user_id=user_id,
            )
        return success


def get_checkin_service() -> CheckinService:
    """Dependency injection for CheckinService."""

    checkin_repo = CheckinRepository()
    spot_repo = SkateSpotRepository()
    return CheckinService(checkin_repo, spot_repo)
