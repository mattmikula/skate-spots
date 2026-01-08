"""Repository for spot condition report persistence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.models import SpotConditionReportORM

if TYPE_CHECKING:  # pragma: no cover
    from datetime import datetime


@dataclass(slots=True)
class ConditionReportCreateData:
    """Data required to create a condition report."""

    spot_id: str
    user_id: str
    surface_quality: str | None
    crowdedness: str | None
    security: str | None
    overall_status: str
    note: str | None
    expires_at: datetime


class ConditionReportRepository:
    """Persistence utilities for spot condition reports."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, payload: ConditionReportCreateData) -> SpotConditionReportORM:
        """Persist a new condition report."""
        report = SpotConditionReportORM(
            spot_id=payload.spot_id,
            user_id=payload.user_id,
            surface_quality=payload.surface_quality,
            crowdedness=payload.crowdedness,
            security=payload.security,
            overall_status=payload.overall_status,
            note=payload.note,
            expires_at=payload.expires_at,
        )
        self.session.add(report)
        self.session.commit()
        self.session.refresh(report)
        return report

    def get_by_id(self, report_id: str) -> SpotConditionReportORM | None:
        """Get a report by ID with user relationship loaded."""
        stmt = (
            select(SpotConditionReportORM)
            .options(joinedload(SpotConditionReportORM.user))
            .where(SpotConditionReportORM.id == report_id)
            .limit(1)
        )
        return self.session.execute(stmt).scalars().first()

    def get_latest_active_for_spot(
        self, spot_id: str, *, now: datetime
    ) -> SpotConditionReportORM | None:
        """Get the most recent active report for a spot.

        Active reports are those that:
        - Have not been deleted (deleted_at IS NULL)
        - Have not expired (expires_at > now)
        """
        stmt = (
            select(SpotConditionReportORM)
            .options(joinedload(SpotConditionReportORM.user))
            .where(
                SpotConditionReportORM.spot_id == spot_id,
                SpotConditionReportORM.deleted_at.is_(None),
                SpotConditionReportORM.expires_at > now,
            )
            .order_by(SpotConditionReportORM.created_at.desc())
            .limit(1)
        )
        return self.session.execute(stmt).scalars().first()

    def list_active_for_spot(
        self, spot_id: str, *, now: datetime, limit: int = 10
    ) -> list[SpotConditionReportORM]:
        """List recent active reports for a spot, ordered by creation time (newest first)."""
        stmt = (
            select(SpotConditionReportORM)
            .options(joinedload(SpotConditionReportORM.user))
            .where(
                SpotConditionReportORM.spot_id == spot_id,
                SpotConditionReportORM.deleted_at.is_(None),
                SpotConditionReportORM.expires_at > now,
            )
            .order_by(SpotConditionReportORM.created_at.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def soft_delete(
        self, report: SpotConditionReportORM, *, deleted_at: datetime
    ) -> SpotConditionReportORM:
        """Soft delete a report by setting the deleted_at timestamp."""
        report.deleted_at = deleted_at
        self.session.commit()
        self.session.refresh(report)
        return report
