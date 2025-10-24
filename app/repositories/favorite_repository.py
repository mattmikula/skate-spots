"""Repository layer for user favorite skate spots."""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db.models import FavoriteSpotORM

SessionFactory = Callable[[], Session]


class FavoriteRepository:
    """Persistence routines for mapping users to their favorite skate spots."""

    def __init__(self, session_factory: SessionFactory | None = None) -> None:
        self._session_factory = session_factory or SessionLocal

    def add(self, user_id: str, spot_id: UUID) -> None:
        """Persist a favorite relationship."""

        with self._session_factory() as session:
            if self._exists(session, user_id, spot_id):
                return
            favorite = FavoriteSpotORM(user_id=user_id, spot_id=str(spot_id))
            session.add(favorite)
            session.commit()

    def remove(self, user_id: str, spot_id: UUID) -> bool:
        """Remove a favorite relationship."""

        with self._session_factory() as session:
            stmt = (
                delete(FavoriteSpotORM)
                .where(
                    FavoriteSpotORM.user_id == user_id,
                    FavoriteSpotORM.spot_id == str(spot_id),
                )
                .execution_options(synchronize_session="fetch")
            )
            result = session.execute(stmt)
            session.commit()
            return result.rowcount is not None and result.rowcount > 0

    def exists(self, user_id: str, spot_id: UUID) -> bool:
        """Return ``True`` if the user has favorited the given spot."""

        with self._session_factory() as session:
            return self._exists(session, user_id, spot_id)

    def list_spot_ids_for_user(self, user_id: str) -> list[UUID]:
        """Return the identifiers for a user's favorite spots ordered by recency."""

        with self._session_factory() as session:
            stmt = (
                select(FavoriteSpotORM.spot_id)
                .where(FavoriteSpotORM.user_id == user_id)
                .order_by(FavoriteSpotORM.created_at.desc())
            )
            return [UUID(spot_id) for (spot_id,) in session.execute(stmt).all()]

    def _exists(self, session: Session, user_id: str, spot_id: UUID) -> bool:
        """Internal helper to test for existence using an active session."""

        stmt = select(FavoriteSpotORM.id).where(
            FavoriteSpotORM.user_id == user_id,
            FavoriteSpotORM.spot_id == str(spot_id),
        )
        return session.execute(stmt).first() is not None
