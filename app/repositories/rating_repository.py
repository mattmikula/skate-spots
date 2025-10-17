"""Repository layer for ratings backed by SQLite."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db.models import RatingORM
from app.models.rating import Rating, RatingCreate, RatingStats, RatingUpdate

SessionFactory = Callable[[], Session]


def _orm_to_pydantic(orm_rating: RatingORM) -> Rating:
    """Convert an ORM instance into a Pydantic model."""

    return Rating(
        id=UUID(orm_rating.id),
        spot_id=UUID(orm_rating.spot_id),
        user_id=UUID(orm_rating.user_id),
        score=orm_rating.score,
        review=orm_rating.review,
        created_at=orm_rating.created_at,
        updated_at=orm_rating.updated_at,
    )


class RatingRepository:
    """Repository handling database persistence for ratings."""

    def __init__(self, session_factory: SessionFactory | None = None) -> None:
        self._session_factory = session_factory or SessionLocal

    def create(self, rating_data: RatingCreate, spot_id: UUID, user_id: str) -> Rating:
        """Create a new rating for a skate spot."""

        orm_rating = RatingORM(
            spot_id=str(spot_id),
            user_id=user_id,
            score=rating_data.score,
            review=rating_data.review,
        )

        with self._session_factory() as session:
            session.add(orm_rating)
            session.commit()
            session.refresh(orm_rating)
            return _orm_to_pydantic(orm_rating)

    def get_by_id(self, rating_id: UUID) -> Rating | None:
        """Get a rating by ID."""

        with self._session_factory() as session:
            orm_rating = session.get(RatingORM, str(rating_id))
            if orm_rating is None:
                return None
            return _orm_to_pydantic(orm_rating)

    def get_by_spot_and_user(self, spot_id: UUID, user_id: str) -> Rating | None:
        """Get a rating for a specific spot by a specific user."""

        with self._session_factory() as session:
            stmt = select(RatingORM).where(
                RatingORM.spot_id == str(spot_id), RatingORM.user_id == user_id
            )
            orm_rating = session.scalars(stmt).first()
            if orm_rating is None:
                return None
            return _orm_to_pydantic(orm_rating)

    def get_by_spot(self, spot_id: UUID) -> list[Rating]:
        """Get all ratings for a skate spot."""

        with self._session_factory() as session:
            stmt = select(RatingORM).where(RatingORM.spot_id == str(spot_id))
            orm_ratings = session.scalars(stmt).all()
            return [_orm_to_pydantic(rating) for rating in orm_ratings]

    def get_stats_for_spot(self, spot_id: UUID) -> RatingStats:
        """Get rating statistics for a skate spot."""

        with self._session_factory() as session:
            stmt = select(RatingORM).where(RatingORM.spot_id == str(spot_id))
            orm_ratings = session.scalars(stmt).all()

            if not orm_ratings:
                return RatingStats(
                    average_score=0, total_ratings=0, distribution={1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
                )

            scores = [rating.score for rating in orm_ratings]
            average = sum(scores) / len(scores)
            distribution = {i: sum(1 for s in scores if s == i) for i in range(1, 6)}

            return RatingStats(
                average_score=round(average, 2),
                total_ratings=len(orm_ratings),
                distribution=distribution,
            )

    def update(self, rating_id: UUID, update_data: RatingUpdate) -> Rating | None:
        """Update an existing rating."""

        updates = update_data.model_dump(exclude_unset=True)

        with self._session_factory() as session:
            orm_rating = session.get(RatingORM, str(rating_id))
            if orm_rating is None:
                return None

            for field, value in updates.items():
                if value is not None:
                    setattr(orm_rating, field, value)

            orm_rating.updated_at = datetime.utcnow()
            session.add(orm_rating)
            session.commit()
            session.refresh(orm_rating)
            return _orm_to_pydantic(orm_rating)

    def delete(self, rating_id: UUID) -> bool:
        """Delete a rating by ID."""

        with self._session_factory() as session:
            orm_rating = session.get(RatingORM, str(rating_id))
            if orm_rating is None:
                return False
            session.delete(orm_rating)
            session.commit()
            return True

    def is_owner(self, rating_id: UUID, user_id: str) -> bool:
        """Check if a user owns a rating."""

        with self._session_factory() as session:
            orm_rating = session.get(RatingORM, str(rating_id))
            if orm_rating is None:
                return False
            return orm_rating.user_id == user_id
