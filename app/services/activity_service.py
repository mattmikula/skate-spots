"""Service for managing activity feed."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Annotated, Any

from fastapi import Depends

from app.core.dependencies import get_db
from app.models.activity import (
    Activity,
    ActivityActor,
    ActivityFeedResponse,
    ActivityType,
    TargetType,
)
from app.repositories.activity_repository import ActivityRepository
from app.repositories.user_repository import UserRepository

if TYPE_CHECKING:
    from app.db.models import ActivityFeedORM


class ActivityService:
    """Service for managing activity feed."""

    def __init__(self, db: Any) -> None:
        """Initialize service with database session."""
        self.db = db
        self.activity_repository = ActivityRepository(db)
        self.user_repository = UserRepository(db)

    def record_spot_created(
        self, user_id: str, spot_id: str, spot_name: str | None = None
    ) -> ActivityFeedORM:
        """Record that a user created a spot.

        Args:
            user_id: ID of the user
            spot_id: ID of the spot created
            spot_name: Optional name of the spot

        Returns:
            Created ActivityFeedORM
        """
        metadata = {"spot_name": spot_name} if spot_name else None
        return self.activity_repository.create_activity(
            user_id=user_id,
            activity_type=ActivityType.SPOT_CREATED.value,
            target_type=TargetType.SPOT.value,
            target_id=spot_id,
            metadata=metadata,
        )

    def record_spot_rated(
        self, user_id: str, spot_id: str, rating_id: str, score: int | None = None
    ) -> ActivityFeedORM:
        """Record that a user rated a spot.

        Args:
            user_id: ID of the user
            spot_id: ID of the rated spot
            rating_id: ID of the rating
            score: Optional rating score

        Returns:
            Created ActivityFeedORM
        """
        metadata = {"spot_id": spot_id, "score": score} if score else {"spot_id": spot_id}
        return self.activity_repository.create_activity(
            user_id=user_id,
            activity_type=ActivityType.SPOT_RATED.value,
            target_type=TargetType.RATING.value,
            target_id=rating_id,
            metadata=metadata,
        )

    def record_spot_commented(self, user_id: str, spot_id: str, comment_id: str) -> ActivityFeedORM:
        """Record that a user commented on a spot.

        Args:
            user_id: ID of the user
            spot_id: ID of the spot
            comment_id: ID of the comment

        Returns:
            Created ActivityFeedORM
        """
        metadata = {"spot_id": spot_id}
        return self.activity_repository.create_activity(
            user_id=user_id,
            activity_type=ActivityType.SPOT_COMMENTED.value,
            target_type=TargetType.COMMENT.value,
            target_id=comment_id,
            metadata=metadata,
        )

    def record_spot_favorited(
        self, user_id: str, spot_id: str, favorite_id: str | None = None
    ) -> ActivityFeedORM:
        """Record that a user favorited a spot.

        Args:
            user_id: ID of the user
            spot_id: ID of the favorited spot
            favorite_id: Optional ID of the favorite record

        Returns:
            Created ActivityFeedORM
        """
        metadata = {"spot_id": spot_id}
        target_id = favorite_id or spot_id  # Use favorite_id if available, otherwise spot_id
        return self.activity_repository.create_activity(
            user_id=user_id,
            activity_type=ActivityType.SPOT_FAVORITED.value,
            target_type=TargetType.FAVORITE.value,
            target_id=target_id,
            metadata=metadata,
        )

    def record_session_created(
        self, user_id: str, session_id: str, session_title: str | None = None
    ) -> ActivityFeedORM:
        """Record that a user created a session.

        Args:
            user_id: ID of the user
            session_id: ID of the session created
            session_title: Optional title of the session

        Returns:
            Created ActivityFeedORM
        """
        metadata = {"session_title": session_title} if session_title else None
        return self.activity_repository.create_activity(
            user_id=user_id,
            activity_type=ActivityType.SESSION_CREATED.value,
            target_type=TargetType.SESSION.value,
            target_id=session_id,
            metadata=metadata,
        )

    def record_session_rsvp(
        self,
        user_id: str,
        session_id: str,
        rsvp_id: str,
        response: str | None = None,
    ) -> ActivityFeedORM:
        """Record that a user RSVPed to a session.

        Args:
            user_id: ID of the user
            session_id: ID of the session
            rsvp_id: ID of the RSVP record
            response: Optional RSVP response (going, maybe, waitlist)

        Returns:
            Created ActivityFeedORM
        """
        metadata = (
            {"session_id": session_id, "response": response}
            if response
            else {"session_id": session_id}
        )
        return self.activity_repository.create_activity(
            user_id=user_id,
            activity_type=ActivityType.SESSION_RSVP.value,
            target_type=TargetType.RSVP.value,
            target_id=rsvp_id,
            metadata=metadata,
        )

    def get_personalized_feed(
        self, user_id: str, limit: int = 20, offset: int = 0
    ) -> ActivityFeedResponse:
        """Get personalized activity feed for a user (activities from followed users).

        Args:
            user_id: ID of the user
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            ActivityFeedResponse with activities
        """
        activities, total = self.activity_repository.get_user_feed(user_id, limit, offset)
        activity_models = self._enrich_activities(activities)

        has_more = (offset + limit) < total

        return ActivityFeedResponse(
            activities=activity_models,
            total=total,
            limit=limit,
            offset=offset,
            has_more=has_more,
        )

    def get_public_feed(self, limit: int = 20, offset: int = 0) -> ActivityFeedResponse:
        """Get public activity feed (all recent activities).

        Args:
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            ActivityFeedResponse with activities
        """
        activities, total = self.activity_repository.get_public_feed(limit, offset)
        activity_models = self._enrich_activities(activities)

        has_more = (offset + limit) < total

        return ActivityFeedResponse(
            activities=activity_models,
            total=total,
            limit=limit,
            offset=offset,
            has_more=has_more,
        )

    def get_user_activity(
        self, user_id: str, limit: int = 20, offset: int = 0
    ) -> ActivityFeedResponse:
        """Get activity history for a specific user.

        Args:
            user_id: ID of the user
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            ActivityFeedResponse with activities
        """
        activities, total = self.activity_repository.get_user_activity(user_id, limit, offset)
        activity_models = self._enrich_activities(activities)

        has_more = (offset + limit) < total

        return ActivityFeedResponse(
            activities=activity_models,
            total=total,
            limit=limit,
            offset=offset,
            has_more=has_more,
        )

    def delete_activities_for_target(self, target_type: str, target_id: str) -> int:
        """Delete all activities related to a target (called when entity is deleted).

        Args:
            target_type: Type of target (spot, rating, comment, etc.)
            target_id: ID of the target

        Returns:
            Number of activities deleted
        """
        return self.activity_repository.delete_activity_by_target(target_type, target_id)

    def _enrich_activities(self, orm_activities: list[ActivityFeedORM]) -> list[Activity]:
        """Convert ORM activities to Pydantic models with enriched actor info.

        Args:
            orm_activities: List of ActivityFeedORM objects

        Returns:
            List of Activity models
        """
        activities = []
        for orm_activity in orm_activities:
            # Get actor info
            actor = None
            user = self.user_repository.get_by_id(orm_activity.user_id)
            if user:
                actor = ActivityActor(
                    id=user.id,
                    username=user.username,
                    display_name=user.display_name,
                    profile_photo_url=user.profile_photo_url,
                )

            # Parse metadata
            metadata = None
            if orm_activity.activity_metadata:
                try:
                    metadata = json.loads(orm_activity.activity_metadata)
                except (json.JSONDecodeError, TypeError):
                    metadata = None

            activity = Activity(
                id=orm_activity.id,
                user_id=orm_activity.user_id,
                activity_type=orm_activity.activity_type,
                target_type=orm_activity.target_type,
                target_id=orm_activity.target_id,
                actor=actor,
                metadata=metadata,
                created_at=orm_activity.created_at,
            )
            activities.append(activity)

        return activities


def get_activity_service(db: Annotated[Any, Depends(get_db)]) -> ActivityService:
    """Get activity service dependency.

    Args:
        db: Database session

    Returns:
        ActivityService instance
    """
    return ActivityService(db)
