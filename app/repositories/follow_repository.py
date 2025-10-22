"""Repository for user follow relationships."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import and_, func, select

from app.db.models import UserFollowORM, UserORM
from app.models.follow import FollowStats

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class FollowRepository:
    """Repository for managing user follow relationships."""

    def __init__(self, session: Session) -> None:
        """Initialize repository with database session."""
        self.session = session

    def follow_user(self, follower_id: str, following_id: str) -> UserFollowORM:
        """Create a follow relationship.

        Args:
            follower_id: ID of the user doing the following
            following_id: ID of the user being followed

        Returns:
            The created UserFollowORM object

        Raises:
            ValueError: If trying to follow yourself or if already following
        """
        if follower_id == following_id:
            raise ValueError("Users cannot follow themselves")

        # Check if already following
        existing = self.session.execute(
            select(UserFollowORM).where(
                and_(
                    UserFollowORM.follower_id == follower_id,
                    UserFollowORM.following_id == following_id,
                )
            )
        ).scalar_one_or_none()

        if existing:
            raise ValueError("Already following this user")

        follow = UserFollowORM(follower_id=follower_id, following_id=following_id)
        self.session.add(follow)
        self.session.commit()
        return follow

    def unfollow_user(self, follower_id: str, following_id: str) -> bool:
        """Remove a follow relationship.

        Args:
            follower_id: ID of the user doing the unfollowing
            following_id: ID of the user being unfollowed

        Returns:
            True if relationship was deleted, False if it didn't exist
        """
        follow = self.session.execute(
            select(UserFollowORM).where(
                and_(
                    UserFollowORM.follower_id == follower_id,
                    UserFollowORM.following_id == following_id,
                )
            )
        ).scalar_one_or_none()

        if not follow:
            return False

        self.session.delete(follow)
        self.session.commit()
        return True

    def is_following(self, follower_id: str, following_id: str) -> bool:
        """Check if user is following another user.

        Args:
            follower_id: ID of the potential follower
            following_id: ID of the user to check

        Returns:
            True if follower_id is following following_id
        """
        follow = self.session.execute(
            select(UserFollowORM).where(
                and_(
                    UserFollowORM.follower_id == follower_id,
                    UserFollowORM.following_id == following_id,
                )
            )
        ).scalar_one_or_none()

        return follow is not None

    def get_followers(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> tuple[list[UserORM], int]:
        """Get users following a specific user.

        Args:
            user_id: ID of the user
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            Tuple of (list of UserORM objects, total count)
        """
        # Get total count efficiently
        total_count = self.session.execute(
            select(func.count(UserFollowORM.id)).where(UserFollowORM.following_id == user_id)
        ).scalar()

        # Get paginated results with user details
        followers = (
            self.session.execute(
                select(UserORM)
                .join(UserFollowORM, UserFollowORM.follower_id == UserORM.id)
                .where(UserFollowORM.following_id == user_id)
                .order_by(UserFollowORM.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            .scalars()
            .all()
        )

        return followers, total_count or 0

    def get_following(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> tuple[list[UserORM], int]:
        """Get users that a specific user is following.

        Args:
            user_id: ID of the user
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            Tuple of (list of UserORM objects, total count)
        """
        # Get total count efficiently
        total_count = self.session.execute(
            select(func.count(UserFollowORM.id)).where(UserFollowORM.follower_id == user_id)
        ).scalar()

        # Get paginated results with user details
        following = (
            self.session.execute(
                select(UserORM)
                .join(UserFollowORM, UserFollowORM.following_id == UserORM.id)
                .where(UserFollowORM.follower_id == user_id)
                .order_by(UserFollowORM.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            .scalars()
            .all()
        )

        return following, total_count or 0

    def get_follow_stats(self, user_id: str) -> FollowStats:
        """Get follower and following counts for a user.

        Args:
            user_id: ID of the user

        Returns:
            FollowStats model with follower and following counts
        """
        followers_count = (
            self.session.execute(
                select(func.count(UserFollowORM.id)).where(UserFollowORM.following_id == user_id)
            ).scalar()
            or 0
        )

        following_count = (
            self.session.execute(
                select(func.count(UserFollowORM.id)).where(UserFollowORM.follower_id == user_id)
            ).scalar()
            or 0
        )

        return FollowStats(
            followers_count=followers_count,
            following_count=following_count,
        )
