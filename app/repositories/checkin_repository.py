"""Repository layer for spot check-ins."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime, timedelta

from sqlalchemy import and_, delete, func, select
from sqlalchemy.orm import Session, joinedload

from app.db.database import SessionLocal
from app.db.models import SpotCheckinORM

SessionFactory = Callable[[], Session]


class CheckinRepository:
    """Persistence routines for spot check-ins."""

    def __init__(self, session_factory: SessionFactory | None = None) -> None:
        self._session_factory = session_factory or SessionLocal

    def create(self, spot_id: str, user_id: str, notes: str | None = None) -> SpotCheckinORM:
        """Create a new check-in record."""

        with self._session_factory() as session:
            checkin = SpotCheckinORM(
                spot_id=spot_id,
                user_id=user_id,
                notes=notes,
                checked_in_at=datetime.utcnow(),
            )
            session.add(checkin)
            session.commit()
            session.refresh(checkin)
            return checkin

    def get_user_checkin_today(self, spot_id: str, user_id: str) -> SpotCheckinORM | None:
        """Get user's check-in for a spot today, if it exists."""

        with self._session_factory() as session:
            today = date.today()
            stmt = select(SpotCheckinORM).where(
                and_(
                    SpotCheckinORM.spot_id == spot_id,
                    SpotCheckinORM.user_id == user_id,
                    func.date(SpotCheckinORM.checked_in_at) == today,
                )
            )
            return session.scalars(stmt).one_or_none()

    def list_for_spot(self, spot_id: str, limit: int = 20) -> list[SpotCheckinORM]:
        """Get recent check-ins for a spot, ordered newest first."""

        with self._session_factory() as session:
            stmt = (
                select(SpotCheckinORM)
                .where(SpotCheckinORM.spot_id == spot_id)
                .order_by(SpotCheckinORM.checked_in_at.desc())
                .limit(limit)
            )
            return session.scalars(stmt).all()

    def list_for_user(self, user_id: str, limit: int = 50) -> list[SpotCheckinORM]:
        """Get user's recent check-ins, ordered newest first."""

        with self._session_factory() as session:
            stmt = (
                select(SpotCheckinORM)
                .options(joinedload(SpotCheckinORM.spot))
                .where(SpotCheckinORM.user_id == user_id)
                .order_by(SpotCheckinORM.checked_in_at.desc())
                .limit(limit)
            )
            return session.scalars(stmt).unique().all()

    def get_stats_for_spot(self, spot_id: str, user_id: str | None = None) -> dict:
        """Get check-in statistics for a spot."""

        with self._session_factory() as session:
            now = datetime.utcnow()
            today = date.today()
            week_ago = now - timedelta(days=7)

            # Total count
            total_stmt = select(func.count(SpotCheckinORM.id)).where(
                SpotCheckinORM.spot_id == spot_id
            )
            total_count = session.scalar(total_stmt) or 0

            # Today count
            today_stmt = select(func.count(SpotCheckinORM.id)).where(
                and_(
                    SpotCheckinORM.spot_id == spot_id,
                    func.date(SpotCheckinORM.checked_in_at) == today,
                )
            )
            today_count = session.scalar(today_stmt) or 0

            # Week count
            week_stmt = select(func.count(SpotCheckinORM.id)).where(
                and_(
                    SpotCheckinORM.spot_id == spot_id,
                    SpotCheckinORM.checked_in_at >= week_ago,
                )
            )
            week_count = session.scalar(week_stmt) or 0

            # User checked in today
            user_checked_in_today = False
            if user_id:
                user_today_stmt = select(func.count(SpotCheckinORM.id)).where(
                    and_(
                        SpotCheckinORM.spot_id == spot_id,
                        SpotCheckinORM.user_id == user_id,
                        func.date(SpotCheckinORM.checked_in_at) == today,
                    )
                )
                user_checked_in_today = (session.scalar(user_today_stmt) or 0) > 0

            return {
                "today_count": today_count,
                "week_count": week_count,
                "total_count": total_count,
                "user_checked_in_today": user_checked_in_today,
            }

    def delete(self, checkin_id: str) -> bool:
        """Delete a check-in."""

        with self._session_factory() as session:
            stmt = delete(SpotCheckinORM).where(SpotCheckinORM.id == checkin_id)
            result = session.execute(stmt)
            session.commit()
            return result.rowcount is not None and result.rowcount > 0

    def get_by_id(self, checkin_id: str) -> SpotCheckinORM | None:
        """Get a check-in by ID."""

        with self._session_factory() as session:
            stmt = select(SpotCheckinORM).where(SpotCheckinORM.id == checkin_id)
            return session.scalars(stmt).one_or_none()
