"""Repository for activity feed."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from sqlalchemy import and_, delete, func, select

from app.db.models import ActivityFeedORM, UserFollowORM

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class ActivityRepository:
    """Repository for managing activity feed."""

    def __init__(self, session: Session) -> None:
        """Initialize repository with database session."""
        self.session = session

    def create_activity(
        self,
        user_id: str,
        activity_type: str,
        target_type: str,
        target_id: str,
        metadata: dict | None = None,
    ) -> ActivityFeedORM:
        """Record a new activity.

        Args:
            user_id: ID of the user performing the activity
            activity_type: Type of activity (e.g., spot_created, spot_rated)
            target_type: Type of target entity (e.g., spot, rating)
            target_id: ID of the target entity
            metadata: Optional additional data about the activity

        Returns:
            The created ActivityFeedORM object
        """
        activity = ActivityFeedORM(
            user_id=user_id,
            activity_type=activity_type,
            target_type=target_type,
            target_id=target_id,
            activity_metadata=json.dumps(metadata) if metadata else None,
        )
        self.session.add(activity)
        self.session.commit()
        return activity

    def get_user_feed(
        self, user_id: str, limit: int = 20, offset: int = 0
    ) -> tuple[list[ActivityFeedORM], int]:
        """Get personalized feed for a user (activities from followed users).

        Args:
            user_id: ID of the user
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            Tuple of (list of activities, total count of activities in feed)
        """
        # Get IDs of users being followed
        followed_users = (
            self.session.execute(
                select(UserFollowORM.following_id).where(UserFollowORM.follower_id == user_id)
            )
            .scalars()
            .all()
        )

        if not followed_users:
            # If not following anyone, return empty list
            return [], 0

        # Get activities from followed users - use efficient count query
        total_count = (
            self.session.execute(
                select(func.count(ActivityFeedORM.id)).where(
                    ActivityFeedORM.user_id.in_(followed_users)
                )
            ).scalar()
            or 0
        )

        activities = (
            self.session.execute(
                select(ActivityFeedORM)
                .where(ActivityFeedORM.user_id.in_(followed_users))
                .order_by(ActivityFeedORM.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            .scalars()
            .all()
        )

        return activities, total_count

    def get_public_feed(
        self, limit: int = 20, offset: int = 0
    ) -> tuple[list[ActivityFeedORM], int]:
        """Get public activity feed (all recent activities).

        Args:
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            Tuple of (list of activities, total count)
        """
        total_count = self.session.execute(select(func.count(ActivityFeedORM.id))).scalar() or 0

        activities = (
            self.session.execute(
                select(ActivityFeedORM)
                .order_by(ActivityFeedORM.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            .scalars()
            .all()
        )

        return activities, total_count

    def get_user_activity(
        self, user_id: str, limit: int = 20, offset: int = 0
    ) -> tuple[list[ActivityFeedORM], int]:
        """Get activity history for a specific user.

        Args:
            user_id: ID of the user
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            Tuple of (list of activities, total count)
        """
        total_count = (
            self.session.execute(
                select(func.count(ActivityFeedORM.id)).where(ActivityFeedORM.user_id == user_id)
            ).scalar()
            or 0
        )

        activities = (
            self.session.execute(
                select(ActivityFeedORM)
                .where(ActivityFeedORM.user_id == user_id)
                .order_by(ActivityFeedORM.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            .scalars()
            .all()
        )

        return activities, total_count

    def delete_activity_by_target(self, target_type: str, target_id: str) -> int:
        """Delete activities related to a specific target (e.g., when spot is deleted).

        Args:
            target_type: Type of target entity
            target_id: ID of the target entity

        Returns:
            Number of activities deleted
        """
        stmt = delete(ActivityFeedORM).where(
            and_(
                ActivityFeedORM.target_type == target_type,
                ActivityFeedORM.target_id == target_id,
            )
        )
        result = self.session.execute(stmt)
        self.session.commit()
        return result.rowcount

    def get_activity_by_id(self, activity_id: str) -> ActivityFeedORM | None:
        """Get a single activity by ID.

        Args:
            activity_id: ID of the activity

        Returns:
            ActivityFeedORM object or None if not found
        """
        activity = self.session.execute(
            select(ActivityFeedORM).where(ActivityFeedORM.id == activity_id)
        ).scalar_one_or_none()
        return activity

    def get_activities_for_target(self, target_type: str, target_id: str) -> list[ActivityFeedORM]:
        """Get all activities related to a specific target.

        Args:
            target_type: Type of target entity
            target_id: ID of the target entity

        Returns:
            List of activities
        """
        activities = (
            self.session.execute(
                select(ActivityFeedORM)
                .where(
                    and_(
                        ActivityFeedORM.target_type == target_type,
                        ActivityFeedORM.target_id == target_id,
                    )
                )
                .order_by(ActivityFeedORM.created_at.desc())
            )
            .scalars()
            .all()
        )
        return activities
