"""Repository helpers for spot check-ins."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime  # noqa: TCH003
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.models import SpotCheckInORM

if TYPE_CHECKING:
    from collections.abc import Iterable


@dataclass(slots=True)
class CheckInCreateData:
    """Payload required to create a spot check-in."""

    spot_id: str
    user_id: str
    status: str
    message: str | None
    expires_at: datetime


class CheckInRepository:
    """Persistence utilities for spot check-ins."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, payload: CheckInCreateData) -> SpotCheckInORM:
        """Persist a new check-in."""

        check_in = SpotCheckInORM(
            spot_id=payload.spot_id,
            user_id=payload.user_id,
            status=payload.status,
            message=payload.message,
            expires_at=payload.expires_at,
        )
        self.session.add(check_in)
        self.session.commit()
        self.session.refresh(check_in)
        return check_in

    def list_active_for_spot(self, spot_id: str, *, now: datetime) -> list[SpotCheckInORM]:
        """Return active check-ins for a spot ordered by recency."""

        stmt = (
            select(SpotCheckInORM)
            .options(joinedload(SpotCheckInORM.user))
            .where(
                SpotCheckInORM.spot_id == spot_id,
                SpotCheckInORM.ended_at.is_(None),
                SpotCheckInORM.expires_at > now,
            )
            .order_by(SpotCheckInORM.created_at.desc())
        )
        return self.session.execute(stmt).scalars().all()

    def get_active_for_user(
        self,
        spot_id: str,
        user_id: str,
        *,
        now: datetime,
    ) -> SpotCheckInORM | None:
        """Return the user's active check-in for a spot if it exists."""

        stmt = (
            select(SpotCheckInORM)
            .options(joinedload(SpotCheckInORM.user))
            .where(
                SpotCheckInORM.spot_id == spot_id,
                SpotCheckInORM.user_id == user_id,
                SpotCheckInORM.ended_at.is_(None),
                SpotCheckInORM.expires_at > now,
            )
            .limit(1)
        )
        return self.session.execute(stmt).scalars().first()

    def get_by_id(self, check_in_id: str) -> SpotCheckInORM | None:
        """Return a check-in by identifier."""

        stmt = (
            select(SpotCheckInORM)
            .options(joinedload(SpotCheckInORM.user))
            .where(SpotCheckInORM.id == check_in_id)
            .limit(1)
        )
        return self.session.execute(stmt).scalars().first()

    def refresh_active(
        self,
        check_in: SpotCheckInORM,
        *,
        status: str,
        message: str | None,
        expires_at: datetime,
    ) -> SpotCheckInORM:
        """Update an active check-in's status/message and extend its expiry."""

        check_in.status = status
        check_in.message = message
        check_in.expires_at = expires_at
        check_in.ended_at = None
        self.session.commit()
        self.session.refresh(check_in)
        return check_in

    def mark_ended(
        self,
        check_in: SpotCheckInORM,
        *,
        ended_at: datetime,
        message: str | None,
    ) -> SpotCheckInORM:
        """Mark a check-in as ended."""

        check_in.ended_at = ended_at
        if message is not None:
            check_in.message = message
        self.session.commit()
        self.session.refresh(check_in)
        return check_in

    def expire_outdated(self, check_ins: Iterable[SpotCheckInORM], *, ended_at: datetime) -> int:
        """Mark provided check-ins as ended (used for cleanup)."""

        updated = 0
        for record in check_ins:
            if record.ended_at is None:
                record.ended_at = ended_at
                updated += 1
        if updated:
            self.session.commit()
        return updated
