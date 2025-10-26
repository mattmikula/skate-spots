"""Repository layer for skate spot ratings."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db.models import RatingORM
from app.models.rating import Rating, RatingCreate, RatingSummary

SessionFactory = Callable[[], Session]


def _orm_to_pydantic(orm_rating: RatingORM) -> Rating:
    """Convert ORM rating to Pydantic representation."""

    return Rating(
        id=UUID(orm_rating.id),
        user_id=UUID(orm_rating.user_id),
        spot_id=UUID(orm_rating.spot_id),
        score=orm_rating.score,
        comment=orm_rating.comment,
        created_at=orm_rating.created_at,
        updated_at=orm_rating.updated_at,
    )


class RatingRepository:
    """Repository for managing persistence of skate spot ratings."""

    def __init__(self, session_factory: SessionFactory | None = None) -> None:
        self._session_factory = session_factory or SessionLocal

    def upsert(self, spot_id: UUID, user_id: str, rating_data: RatingCreate) -> Rating:
        """Create or update the current user's rating for a spot."""

        with self._session_factory() as session:
            orm_rating = (
                session.query(RatingORM)
                .filter(
                    RatingORM.spot_id == str(spot_id),
                    RatingORM.user_id == str(user_id),
                )
                .one_or_none()
            )

            if orm_rating is None:
                orm_rating = RatingORM(
                    spot_id=str(spot_id),
                    user_id=str(user_id),
                    score=rating_data.score,
                    comment=rating_data.comment,
                )
                session.add(orm_rating)
            else:
                orm_rating.score = rating_data.score
                orm_rating.comment = rating_data.comment
                orm_rating.updated_at = datetime.now(UTC)

            session.commit()
            session.refresh(orm_rating)
            return _orm_to_pydantic(orm_rating)

    def get_user_rating(self, spot_id: UUID, user_id: str) -> Rating | None:
        """Return the rating submitted by the given user for the spot."""

        with self._session_factory() as session:
            orm_rating = (
                session.query(RatingORM)
                .filter(
                    RatingORM.spot_id == str(spot_id),
                    RatingORM.user_id == str(user_id),
                )
                .one_or_none()
            )
            return _orm_to_pydantic(orm_rating) if orm_rating is not None else None

    def delete_rating(self, spot_id: UUID, user_id: str) -> bool:
        """Delete the current user's rating for a spot."""

        with self._session_factory() as session:
            orm_rating = (
                session.query(RatingORM)
                .filter(
                    RatingORM.spot_id == str(spot_id),
                    RatingORM.user_id == str(user_id),
                )
                .one_or_none()
            )
            if orm_rating is None:
                return False

            session.delete(orm_rating)
            session.commit()
            return True

    def get_summary(self, spot_id: UUID) -> RatingSummary:
        """Compute aggregate rating statistics for the given spot."""

        with self._session_factory() as session:
            stmt = (
                select(func.count(RatingORM.id), func.avg(RatingORM.score))
                .where(RatingORM.spot_id == str(spot_id))
                .group_by(RatingORM.spot_id)
            )
            result = session.execute(stmt).one_or_none()

            if result is None:
                return RatingSummary(average_score=None, ratings_count=0)

            count, average = result
            count_value = int(count) if count is not None else 0
            average_value = float(average) if average is not None else None
            if average_value is not None:
                average_value = round(average_value, 2)

            return RatingSummary(average_score=average_value, ratings_count=count_value)
