"""Repository for cached weather snapshots."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import select

from app.db.models import WeatherSnapshotORM

if TYPE_CHECKING:
    from datetime import datetime

    from sqlalchemy.orm import Session


class WeatherRepository:
    """Persist and retrieve cached weather responses."""

    def __init__(self, db_session: Session) -> None:
        self._db = db_session

    def get_for_spot(self, spot_id: str) -> WeatherSnapshotORM | None:
        """Return the cached snapshot for a spot if present."""

        stmt = select(WeatherSnapshotORM).where(WeatherSnapshotORM.spot_id == spot_id)
        record = self._db.execute(stmt).scalar_one_or_none()
        if record:
            self._db.expunge(record)
        return record

    def save_snapshot(
        self,
        *,
        spot_id: str,
        provider: str,
        payload: dict[str, Any],
        fetched_at: datetime,
        expires_at: datetime,
    ) -> WeatherSnapshotORM:
        """Insert or update a cached snapshot."""

        existing = (
            self._db.query(WeatherSnapshotORM).filter(WeatherSnapshotORM.spot_id == spot_id).first()
        )

        if existing:
            existing.provider = provider
            existing.payload = payload
            existing.fetched_at = fetched_at
            existing.expires_at = expires_at
            record = existing
        else:
            record = WeatherSnapshotORM(
                spot_id=spot_id,
                provider=provider,
                payload=payload,
                fetched_at=fetched_at,
                expires_at=expires_at,
            )
            self._db.add(record)

        self._db.commit()
        self._db.refresh(record)
        return record

    def delete_for_spot(self, spot_id: str) -> None:
        """Remove cached weather for a given spot."""

        self._db.query(WeatherSnapshotORM).filter(WeatherSnapshotORM.spot_id == spot_id).delete()
        self._db.commit()

    def purge_expired(self, now: datetime) -> int:
        """Delete snapshots that are fully stale."""

        result = (
            self._db.query(WeatherSnapshotORM)
            .filter(WeatherSnapshotORM.expires_at < now)
            .delete(synchronize_session=False)
        )
        self._db.commit()
        return int(result or 0)
