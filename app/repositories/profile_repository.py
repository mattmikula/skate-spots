"""Repository for user profile database operations."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db.database import SessionLocal
from app.db.models import (
    RatingORM,
    SkateSpotORM,
    SpotCommentORM,
    SpotPhotoORM,
    UserORM,
)
from app.models.comment import Comment, CommentAuthor
from app.models.profile import ActivityItem, ActivityType, PublicUserInfo, UserStatistics
from app.models.rating import Rating
from app.models.skate_spot import SkateSpot

if TYPE_CHECKING:
    from uuid import UUID

SessionFactory = Callable[[], Session]


class ProfileRepository:
    """Repository for managing user profile database operations."""

    def __init__(self, session_factory: SessionFactory | None = None) -> None:
        """Initialize the repository with a session factory."""
        self._session_factory = session_factory or SessionLocal

    def get_user_by_username(self, username: str) -> UserORM | None:
        """Get a user by username."""
        with self._session_factory() as session:
            stmt = select(UserORM).where(UserORM.username == username)
            return session.scalars(stmt).one_or_none()

    def get_user_by_id(self, user_id: UUID | str) -> UserORM | None:
        """Get a user by ID."""
        with self._session_factory() as session:
            stmt = select(UserORM).where(UserORM.id == str(user_id))
            return session.scalars(stmt).one_or_none()

    def get_user_statistics(self, user_id: UUID | str) -> UserStatistics:
        """Get statistics for a user's activity."""
        user_id_str = str(user_id)

        with self._session_factory() as session:
            # Count spots added
            spots_added = (
                session.query(func.count(SkateSpotORM.id))
                .filter(SkateSpotORM.user_id == user_id_str)
                .scalar()
                or 0
            )

            # Count photos uploaded
            photos_uploaded = (
                session.query(func.count(SpotPhotoORM.id))
                .filter(SpotPhotoORM.uploader_id == user_id_str)
                .scalar()
                or 0
            )

            # Count comments posted
            comments_posted = (
                session.query(func.count(SpotCommentORM.id))
                .filter(SpotCommentORM.user_id == user_id_str)
                .scalar()
                or 0
            )

            # Count ratings given
            ratings_given = (
                session.query(func.count(RatingORM.id))
                .filter(RatingORM.user_id == user_id_str)
                .scalar()
                or 0
            )

            return UserStatistics(
                spots_added=spots_added,
                photos_uploaded=photos_uploaded,
                comments_posted=comments_posted,
                ratings_given=ratings_given,
            )

    def get_recent_spots(self, user_id: UUID | str, limit: int = 5) -> list[SkateSpot]:
        """Get recently added spots by a user."""
        with self._session_factory() as session:
            spots = (
                session.query(SkateSpotORM)
                .filter(SkateSpotORM.user_id == str(user_id))
                .order_by(SkateSpotORM.created_at.desc())
                .limit(limit)
                .all()
            )

            return [self._spot_orm_to_pydantic(spot) for spot in spots]

    def get_recent_comments(self, user_id: UUID | str, limit: int = 5) -> list[Comment]:
        """Get recently posted comments by a user."""
        with self._session_factory() as session:
            stmt = (
                select(SpotCommentORM)
                .options(selectinload(SpotCommentORM.author))
                .where(SpotCommentORM.user_id == str(user_id))
                .order_by(SpotCommentORM.created_at.desc())
                .limit(limit)
            )
            comments = session.scalars(stmt).all()

            return [self._comment_orm_to_pydantic(comment) for comment in comments]

    def get_recent_ratings(self, user_id: UUID | str, limit: int = 5) -> list[Rating]:
        """Get recently given ratings by a user."""
        with self._session_factory() as session:
            ratings = (
                session.query(RatingORM)
                .filter(RatingORM.user_id == str(user_id))
                .order_by(RatingORM.created_at.desc())
                .limit(limit)
                .all()
            )

            return [self._rating_orm_to_pydantic(rating) for rating in ratings]

    def get_user_activity(self, user_id: UUID | str, limit: int = 10) -> list[ActivityItem]:
        """Get recent activity for a user across all activity types."""
        user_id_str = str(user_id)

        with self._session_factory() as session:
            activities = []

            # Get spots created
            spots = (
                session.query(SkateSpotORM)
                .filter(SkateSpotORM.user_id == user_id_str)
                .order_by(SkateSpotORM.created_at.desc())
                .limit(limit)
                .all()
            )

            for spot in spots:
                activities.append(
                    ActivityItem(
                        activity_type=ActivityType.SPOT_CREATED,
                        timestamp=spot.created_at,
                        spot_id=spot.id,
                        spot_name=spot.name,
                        details=f"Added a {spot.spot_type} spot",
                    )
                )

            # Get photos uploaded
            photos = (
                session.query(SpotPhotoORM)
                .join(SkateSpotORM, SpotPhotoORM.spot_id == SkateSpotORM.id)
                .filter(SpotPhotoORM.uploader_id == user_id_str)
                .order_by(SpotPhotoORM.created_at.desc())
                .limit(limit)
                .all()
            )

            for photo in photos:
                spot = photo.spot
                activities.append(
                    ActivityItem(
                        activity_type=ActivityType.PHOTO_UPLOADED,
                        timestamp=photo.created_at,
                        spot_id=spot.id,
                        spot_name=spot.name,
                        details="Uploaded a photo",
                    )
                )

            # Get comments posted
            comments = (
                session.query(SpotCommentORM)
                .join(SkateSpotORM, SpotCommentORM.spot_id == SkateSpotORM.id)
                .filter(SpotCommentORM.user_id == user_id_str)
                .order_by(SpotCommentORM.created_at.desc())
                .limit(limit)
                .all()
            )

            for comment in comments:
                spot = comment.spot
                activities.append(
                    ActivityItem(
                        activity_type=ActivityType.COMMENT_POSTED,
                        timestamp=comment.created_at,
                        spot_id=spot.id,
                        spot_name=spot.name,
                        details=f"Commented: {comment.content[:50]}...",
                    )
                )

            # Get ratings given
            ratings = (
                session.query(RatingORM)
                .join(SkateSpotORM, RatingORM.spot_id == SkateSpotORM.id)
                .filter(RatingORM.user_id == user_id_str)
                .order_by(RatingORM.created_at.desc())
                .limit(limit)
                .all()
            )

            for rating in ratings:
                spot = rating.spot
                activities.append(
                    ActivityItem(
                        activity_type=ActivityType.RATING_GIVEN,
                        timestamp=rating.created_at,
                        spot_id=spot.id,
                        spot_name=spot.name,
                        details=f"Rated {rating.score}/5",
                    )
                )

            # Sort all activities by timestamp and limit to the requested number
            activities.sort(key=lambda x: x.timestamp, reverse=True)
            return activities[:limit]

    def _spot_orm_to_pydantic(self, spot: SkateSpotORM) -> SkateSpot:
        """Convert a SkateSpotORM to SkateSpot Pydantic model."""
        from app.models.skate_spot import Location, SpotPhoto

        photos = []
        for photo in spot.photos:
            photos.append(
                SpotPhoto(
                    id=photo.id,
                    path=photo.file_path,
                    original_filename=photo.original_filename,
                    created_at=photo.created_at,
                )
            )

        # Calculate rating summary
        rating_count = len(spot.ratings)
        average_rating = None
        if rating_count > 0:
            total_score = sum(rating.score for rating in spot.ratings)
            average_rating = round(total_score / rating_count, 2)

        return SkateSpot(
            id=spot.id,
            name=spot.name,
            description=spot.description,
            spot_type=spot.spot_type,
            difficulty=spot.difficulty,
            location=Location(
                latitude=spot.latitude,
                longitude=spot.longitude,
                address=spot.address,
                city=spot.city,
                country=spot.country,
            ),
            is_public=spot.is_public,
            requires_permission=spot.requires_permission,
            created_at=spot.created_at,
            updated_at=spot.updated_at,
            average_rating=average_rating,
            ratings_count=rating_count,
            photos=photos,
        )

    def _comment_orm_to_pydantic(self, comment: SpotCommentORM) -> Comment:
        """Convert a SpotCommentORM to Comment Pydantic model."""
        return Comment(
            id=comment.id,
            spot_id=comment.spot_id,
            user_id=comment.user_id,
            content=comment.content,
            author=CommentAuthor(id=comment.author.id, username=comment.author.username),
            created_at=comment.created_at,
            updated_at=comment.updated_at,
        )

    def _rating_orm_to_pydantic(self, rating: RatingORM) -> Rating:
        """Convert a RatingORM to Rating Pydantic model."""
        return Rating(
            id=rating.id,
            user_id=rating.user_id,
            spot_id=rating.spot_id,
            score=rating.score,
            comment=rating.comment,
            created_at=rating.created_at,
            updated_at=rating.updated_at,
        )

    def _user_orm_to_public_info(self, user: UserORM) -> PublicUserInfo:
        """Convert a UserORM to PublicUserInfo Pydantic model."""
        return PublicUserInfo(
            id=user.id,
            username=user.username,
            created_at=user.created_at,
        )
