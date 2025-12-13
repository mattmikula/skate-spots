"""Business logic for spot condition reports."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Annotated, Any
from uuid import UUID

from fastapi import Depends

from app.core.dependencies import get_db
from app.core.logging import get_logger
from app.db.models import SkateSpotORM, SpotConditionReportORM, UserORM
from app.models.activity import ActivityActor
from app.models.condition_report import SpotConditionReport, SpotConditionReportCreate
from app.repositories.condition_report_repository import (
    ConditionReportCreateData,
    ConditionReportRepository,
)

if TYPE_CHECKING:  # pragma: no cover
    from app.services.activity_service import ActivityService


class ConditionReportError(Exception):
    """Base class for condition report errors."""


class ConditionReportNotFoundError(ConditionReportError):
    """Raised when a condition report cannot be located."""


class ConditionReportSpotNotFoundError(ConditionReportError):
    """Raised when a skate spot cannot be found."""


class ConditionReportPermissionError(ConditionReportError):
    """Raised when a user attempts an action they are not allowed to perform."""


class ConditionReportService:
    """Coordinate spot condition report persistence and notifications."""

    def __init__(
        self,
        db_session: Any,
        repository: ConditionReportRepository | None = None,
        activity_service: ActivityService | None = None,
    ) -> None:
        self._db = db_session
        self._repo = repository or ConditionReportRepository(db_session)
        self._activity = activity_service
        self._logger = get_logger(__name__)

    def set_activity_service(self, activity_service: ActivityService) -> None:
        """Inject activity service after initialization."""

        self._activity = activity_service

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def create_report(
        self,
        spot_id: UUID,
        user: UserORM,
        payload: SpotConditionReportCreate,
    ) -> SpotConditionReport:
        """Create a new condition report for the spot."""

        spot = self._ensure_spot_exists(spot_id)
        now = self._now()
        expires_at = now + timedelta(hours=24)

        report = self._repo.create(
            ConditionReportCreateData(
                spot_id=str(spot_id),
                user_id=user.id,
                surface_quality=payload.surface_quality.value if payload.surface_quality else None,
                crowdedness=payload.crowdedness.value if payload.crowdedness else None,
                security=payload.security.value if payload.security else None,
                overall_status=payload.overall_status.value,
                note=payload.note,
                expires_at=expires_at,
            )
        )
        self._logger.info(
            "condition report created",
            report_id=report.id,
            spot_id=str(spot_id),
            user_id=user.id,
            overall_status=payload.overall_status.value,
        )

        if self._activity:
            try:
                self._activity.record_spot_condition_reported(
                    user_id=user.id,
                    spot_id=str(spot_id),
                    report_id=str(report.id),
                    overall_status=payload.overall_status.value,
                    spot_name=spot.name,
                    surface_quality=payload.surface_quality.value
                    if payload.surface_quality
                    else None,
                    crowdedness=payload.crowdedness.value if payload.crowdedness else None,
                    security=payload.security.value if payload.security else None,
                )
            except Exception as exc:  # pragma: no cover - defensive logging
                self._logger.warning("failed to record condition report activity", error=str(exc))

        return self._to_model(report, now=self._now())

    def get_latest_for_spot(self, spot_id: UUID) -> SpotConditionReport | None:
        """Get the latest active condition report for a spot."""

        self._ensure_spot_exists(spot_id)
        now = self._now()
        report = self._repo.get_latest_active_for_spot(str(spot_id), now=now)
        return self._to_model(report, now=now) if report else None

    def list_for_spot(self, spot_id: UUID, *, limit: int = 10) -> list[SpotConditionReport]:
        """List recent active condition reports for a spot."""

        self._ensure_spot_exists(spot_id)
        now = self._now()
        reports = self._repo.list_active_for_spot(str(spot_id), now=now, limit=limit)
        return [self._to_model(report, now=now) for report in reports]

    def delete_report(self, report_id: UUID, user: UserORM) -> SpotConditionReport:
        """Soft delete a condition report."""

        report = self._repo.get_by_id(str(report_id))
        if report is None:
            raise ConditionReportNotFoundError("Condition report not found.")

        if report.user_id != user.id and not user.is_admin:
            raise ConditionReportPermissionError(
                "You are not allowed to delete this condition report."
            )

        if report.deleted_at is not None:
            return self._to_model(report, now=self._now())

        deleted_at = self._now()
        updated = self._repo.soft_delete(report, deleted_at=deleted_at)
        self._logger.info(
            "condition report deleted",
            report_id=str(report_id),
            user_id=user.id,
        )
        return self._to_model(updated, now=self._now())

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _ensure_spot_exists(self, spot_id: UUID) -> SkateSpotORM:
        spot = self._db.get(SkateSpotORM, str(spot_id))
        if spot is None:
            self._logger.warning(
                "condition report requested for missing spot", spot_id=str(spot_id)
            )
            raise ConditionReportSpotNotFoundError(f"Skate spot with id {spot_id} not found.")
        return spot

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC)

    def _to_model(self, record: SpotConditionReportORM, *, now: datetime) -> SpotConditionReport:
        """Convert ORM condition report to API model."""

        from app.models.condition_report import (
            ConditionCrowdedness,
            ConditionOverallStatus,
            ConditionSecurity,
            ConditionSurfaceQuality,
        )

        reporter = ActivityActor(
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
        is_active = record.deleted_at is None and expires_at > now

        return SpotConditionReport(
            id=UUID(record.id),
            spot_id=UUID(record.spot_id),
            user_id=UUID(record.user_id),
            surface_quality=ConditionSurfaceQuality(record.surface_quality)
            if record.surface_quality
            else None,
            crowdedness=ConditionCrowdedness(record.crowdedness) if record.crowdedness else None,
            security=ConditionSecurity(record.security) if record.security else None,
            overall_status=ConditionOverallStatus(record.overall_status),
            note=record.note,
            expires_at=record.expires_at,
            deleted_at=record.deleted_at,
            created_at=record.created_at,
            updated_at=record.updated_at,
            is_active=is_active,
            reporter=reporter,
        )


def get_condition_report_service(
    db: Annotated[Any, Depends(get_db)],
) -> ConditionReportService:
    """FastAPI dependency for the condition report service."""

    from app.services.activity_service import get_activity_service

    activity_service = get_activity_service(db)
    service = ConditionReportService(db, activity_service=activity_service)
    return service
