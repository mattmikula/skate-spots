"""Business logic for real-time skate spot check-ins."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Annotated, Any
from uuid import UUID

from fastapi import Depends

from app.core.dependencies import get_db
from app.core.logging import get_logger
from app.db.models import SkateSpotORM, SpotCheckInORM, UserORM
from app.models.activity import ActivityActor
from app.models.check_in import (
    SpotCheckIn,
    SpotCheckInCreate,
    SpotCheckInStatus,
    SpotCheckOut,
)
from app.repositories.check_in_repository import CheckInCreateData, CheckInRepository

if TYPE_CHECKING:  # pragma: no cover
    from app.services.activity_service import ActivityService

DEFAULT_TTL_MINUTES = 120
MIN_TTL_MINUTES = 15
MAX_TTL_MINUTES = 240


class SpotCheckInError(Exception):
    """Base class for check-in errors."""


class SpotCheckInNotFoundError(SpotCheckInError):
    """Raised when a check-in cannot be located."""


class SpotCheckInSpotNotFoundError(SpotCheckInError):
    """Raised when a skate spot cannot be found."""


class SpotCheckInPermissionError(SpotCheckInError):
    """Raised when a user attempts an action they are not allowed to perform."""


class CheckInService:
    """Coordinate spot check-in persistence and notifications."""

    def __init__(
        self,
        db_session: Any,
        repository: CheckInRepository | None = None,
        activity_service: ActivityService | None = None,
    ) -> None:
        self._db = db_session
        self._repo = repository or CheckInRepository(db_session)
        self._activity = activity_service
        self._logger = get_logger(__name__)

    def set_activity_service(self, activity_service: ActivityService) -> None:
        """Inject activity service after initialization."""

        self._activity = activity_service

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def list_active(self, spot_id: UUID) -> list[SpotCheckIn]:
        """Return all active check-ins for the spot."""

        self._ensure_spot_exists(spot_id)
        now = self._now()
        check_ins = self._repo.list_active_for_spot(str(spot_id), now=now)
        return [self._to_model(record, now=now) for record in check_ins]

    def get_active_for_user(self, spot_id: UUID, user_id: str) -> SpotCheckIn | None:
        """Return the current user's active check-in for the spot."""

        self._ensure_spot_exists(spot_id)
        now = self._now()
        record = self._repo.get_active_for_user(str(spot_id), user_id, now=now)
        return self._to_model(record, now=now) if record else None

    def check_in(
        self,
        spot_id: UUID,
        user: UserORM,
        payload: SpotCheckInCreate,
    ) -> SpotCheckIn:
        """Create or refresh a check-in for the user at the spot."""

        spot = self._ensure_spot_exists(spot_id)
        now = self._now()
        ttl_minutes = self._clamp_ttl(payload.ttl_minutes)
        expires_at = now + timedelta(minutes=ttl_minutes)
        message = self._normalise_message(payload.message)

        existing = self._repo.get_active_for_user(str(spot_id), user.id, now=now)
        created_new = existing is None
        previous_status = existing.status if existing else None

        if existing:
            message_to_store = message if message is not None else existing.message
            check_in = self._repo.refresh_active(
                existing,
                status=payload.status.value,
                message=message_to_store,
                expires_at=expires_at,
            )
            self._logger.debug(
                "check-in refreshed",
                check_in_id=check_in.id,
                spot_id=str(spot_id),
                user_id=user.id,
                status=payload.status.value,
            )
        else:
            check_in = self._repo.create(
                CheckInCreateData(
                    spot_id=str(spot_id),
                    user_id=user.id,
                    status=payload.status.value,
                    message=message,
                    expires_at=expires_at,
                )
            )
            self._logger.info(
                "check-in created",
                check_in_id=check_in.id,
                spot_id=str(spot_id),
                user_id=user.id,
                status=payload.status.value,
            )

        if self._activity and (created_new or previous_status != payload.status.value):
            try:
                self._activity.record_spot_check_in(
                    user_id=user.id,
                    spot_id=str(spot_id),
                    check_in_id=str(check_in.id),
                    status=payload.status.value,
                    spot_name=spot.name,
                )
            except Exception as exc:  # pragma: no cover - defensive logging
                self._logger.warning("failed to record check-in activity", error=str(exc))

        return self._to_model(check_in, now=self._now())

    def check_out(
        self,
        check_in_id: UUID,
        user: UserORM,
        payload: SpotCheckOut | None = None,
    ) -> SpotCheckIn:
        """Mark the check-in as inactive."""

        record = self._repo.get_by_id(str(check_in_id))
        if record is None:
            raise SpotCheckInNotFoundError("Check-in not found.")

        if record.user_id != user.id and not user.is_admin:
            raise SpotCheckInPermissionError("You are not allowed to end this check-in.")

        if record.ended_at is not None:
            return self._to_model(record, now=self._now())

        message = self._normalise_message(payload.message) if payload else record.message
        if payload and payload.message is None:
            # Explicitly clear message when None is provided
            message = None
        ended_at = self._now()
        updated = self._repo.mark_ended(record, ended_at=ended_at, message=message)
        self._logger.info(
            "check-in ended",
            check_in_id=str(check_in_id),
            user_id=user.id,
        )
        return self._to_model(updated, now=self._now())

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _ensure_spot_exists(self, spot_id: UUID) -> SkateSpotORM:
        spot = self._db.get(SkateSpotORM, str(spot_id))
        if spot is None:
            self._logger.warning("check-in requested for missing spot", spot_id=str(spot_id))
            raise SpotCheckInSpotNotFoundError(f"Skate spot with id {spot_id} not found.")
        return spot

    @staticmethod
    def _normalise_message(message: str | None) -> str | None:
        if message is None:
            return None
        stripped = message.strip()
        return stripped if stripped else None

    @staticmethod
    def _clamp_ttl(requested: int | None) -> int:
        ttl = requested or DEFAULT_TTL_MINUTES
        return max(MIN_TTL_MINUTES, min(MAX_TTL_MINUTES, ttl))

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC)

    def _to_model(self, record: SpotCheckInORM, *, now: datetime) -> SpotCheckIn:
        """Convert ORM check-in to API model."""

        status = SpotCheckInStatus(record.status)
        actor = ActivityActor(
            id=UUID(record.user.id),
            username=record.user.username,
            display_name=record.user.display_name,
            profile_photo_url=record.user.profile_photo_url,
        )
        # Ensure expires_at is timezone-aware for comparison
        expires_at = (
            record.expires_at.replace(tzinfo=UTC)
            if record.expires_at.tzinfo is None
            else record.expires_at
        )
        is_active = record.ended_at is None and expires_at > now
        return SpotCheckIn(
            id=UUID(record.id),
            spot_id=UUID(record.spot_id),
            user_id=UUID(record.user_id),
            status=status,
            message=record.message,
            expires_at=record.expires_at,
            ended_at=record.ended_at,
            created_at=record.created_at,
            updated_at=record.updated_at,
            is_active=is_active,
            actor=actor,
        )


def get_check_in_service(
    db: Annotated[Any, Depends(get_db)],
) -> CheckInService:
    """FastAPI dependency for the check-in service."""

    from app.services.activity_service import get_activity_service

    activity_service = get_activity_service(db)
    service = CheckInService(db, activity_service=activity_service)
    return service
