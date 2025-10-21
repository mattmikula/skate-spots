"""Repository helpers for assembling public user profile data."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.database import SessionLocal
from app.db.models import (
    RatingORM,
    SkateSpotORM,
    SpotCommentORM,
    SpotPhotoORM,
    UserORM,
)
from app.models.user_profile import (
    UserActivityItem,
    UserActivityType,
    UserCommentSummary,
    UserProfile,
    UserProfileStats,
    UserRatingSummary,
    UserSpotSummary,
)

SessionFactory = Callable[[], Session]


class UserProfileRepository:
    """Aggregate user contributions into structured profile data."""

    def __init__(self, session_factory: SessionFactory | None = None) -> None:
        self._session_factory = session_factory or SessionLocal

    def get_by_username(self, username: str) -> UserProfile | None:
        """Return a populated profile for the given username, if found."""

        with self._session_factory() as session:
            stmt = (
                select(UserORM)
                .options(
                    selectinload(UserORM.skate_spots).selectinload(SkateSpotORM.photos),
                    selectinload(UserORM.skate_spots).selectinload(SkateSpotORM.ratings),
                    selectinload(UserORM.comments).selectinload(SpotCommentORM.spot),
                    selectinload(UserORM.ratings).selectinload(RatingORM.spot),
                    selectinload(UserORM.uploaded_photos).selectinload(SpotPhotoORM.spot),
                )
                .where(UserORM.username == username)
            )
            orm_user = session.scalars(stmt).unique().one_or_none()
            if orm_user is None:
                return None

            return self._build_profile(orm_user)

    def _build_profile(self, user: UserORM) -> UserProfile:
        spots = sorted(user.skate_spots, key=lambda spot: spot.created_at, reverse=True)
        comments = sorted(user.comments, key=lambda comment: comment.created_at, reverse=True)
        ratings = sorted(user.ratings, key=lambda rating: rating.created_at, reverse=True)
        photos = sorted(user.uploaded_photos, key=lambda photo: photo.created_at, reverse=True)

        stats = UserProfileStats(
            spots_added=len(spots),
            photos_uploaded=len(photos),
            comments_posted=len(comments),
            ratings_left=len(ratings),
            average_rating_given=self._average_rating_given(ratings),
        )

        spot_summaries = [self._spot_summary(spot) for spot in spots[:12]]
        comment_summaries = [self._comment_summary(comment) for comment in comments[:10]]
        rating_summaries = [self._rating_summary(rating) for rating in ratings[:10]]

        activity = self._activity_feed(spots, comments, ratings, photos)

        return UserProfile(
            id=UUID(user.id),
            username=user.username,
            display_name=user.display_name,
            bio=user.bio,
            location=user.location,
            website_url=user.website_url,
            instagram_handle=user.instagram_handle,
            profile_photo_url=user.profile_photo_url,
            joined_at=user.created_at,
            stats=stats,
            spots=spot_summaries,
            recent_comments=comment_summaries,
            recent_ratings=rating_summaries,
            activity=activity,
        )

    @staticmethod
    def _average_rating_given(ratings: Iterable[RatingORM]) -> float | None:
        scores = [rating.score for rating in ratings]
        if not scores:
            return None
        average = sum(scores) / len(scores)
        return round(average, 2)

    @staticmethod
    def _spot_summary(spot: SkateSpotORM) -> UserSpotSummary:
        ratings = [rating.score for rating in spot.ratings]
        average_rating = round(sum(ratings) / len(ratings), 2) if ratings else None

        return UserSpotSummary(
            id=UUID(spot.id),
            name=spot.name,
            city=spot.city,
            country=spot.country,
            created_at=spot.created_at,
            photo_count=len(spot.photos),
            average_rating=average_rating,
            ratings_count=len(ratings),
        )

    @staticmethod
    def _comment_summary(comment: SpotCommentORM) -> UserCommentSummary:
        spot_name = comment.spot.name if comment.spot is not None else "Unknown spot"
        return UserCommentSummary(
            id=UUID(comment.id),
            spot_id=UUID(comment.spot_id),
            spot_name=spot_name,
            content=comment.content,
            created_at=comment.created_at,
        )

    @staticmethod
    def _rating_summary(rating: RatingORM) -> UserRatingSummary:
        spot_name = rating.spot.name if rating.spot is not None else "Unknown spot"
        return UserRatingSummary(
            id=UUID(rating.id),
            spot_id=UUID(rating.spot_id),
            spot_name=spot_name,
            score=rating.score,
            comment=rating.comment,
            created_at=rating.created_at,
        )

    def _activity_feed(
        self,
        spots: list[SkateSpotORM],
        comments: list[SpotCommentORM],
        ratings: list[RatingORM],
        photos: list[SpotPhotoORM],
    ) -> list[UserActivityItem]:
        entries: list[UserActivityItem] = []

        for spot in spots:
            entries.append(
                UserActivityItem(
                    type=UserActivityType.SPOT_CREATED,
                    created_at=spot.created_at,
                    spot_id=UUID(spot.id),
                    spot_name=spot.name,
                )
            )

        for comment in comments:
            entries.append(
                UserActivityItem(
                    type=UserActivityType.COMMENTED,
                    created_at=comment.created_at,
                    spot_id=UUID(comment.spot_id),
                    spot_name=comment.spot.name if comment.spot else None,
                    comment=comment.content,
                )
            )

        for rating in ratings:
            entries.append(
                UserActivityItem(
                    type=UserActivityType.RATED,
                    created_at=rating.created_at,
                    spot_id=UUID(rating.spot_id),
                    spot_name=rating.spot.name if rating.spot else None,
                    rating_score=rating.score,
                    comment=rating.comment,
                )
            )

        for photo in photos:
            spot_name = photo.spot.name if photo.spot else None
            entries.append(
                UserActivityItem(
                    type=UserActivityType.PHOTO_UPLOADED,
                    created_at=photo.created_at,
                    spot_id=UUID(photo.spot_id) if photo.spot_id else None,
                    spot_name=spot_name,
                    photo_path=photo.file_path,
                )
            )

        entries.sort(key=lambda item: item.created_at, reverse=True)
        return entries[:20]
