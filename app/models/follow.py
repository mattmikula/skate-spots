"""Pydantic models for user follow relationships."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class UserFollowBase(BaseModel):
    """Base model for user follow relationships."""

    pass


class UserFollowCreate(UserFollowBase):
    """Model for creating a follow relationship."""

    pass


class FollowerUser(BaseModel):
    """Simplified user model for follower listings."""

    id: UUID
    username: str
    display_name: str | None = None
    profile_photo_url: str | None = None

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class UserFollow(UserFollowBase):
    """Model representing a persisted follow relationship."""

    id: UUID
    follower_id: UUID
    following_id: UUID
    created_at: datetime

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class FollowStats(BaseModel):
    """Follower and following statistics for a user."""

    followers_count: int = Field(0, ge=0)
    following_count: int = Field(0, ge=0)


class FollowersResponse(BaseModel):
    """Response containing a list of followers."""

    followers: list[FollowerUser]
    total: int = Field(..., ge=0)
    limit: int = Field(..., ge=0)
    offset: int = Field(..., ge=0)


class FollowingResponse(BaseModel):
    """Response containing a list of users being followed."""

    following: list[FollowerUser]
    total: int = Field(..., ge=0)
    limit: int = Field(..., ge=0)
    offset: int = Field(..., ge=0)


class IsFollowingResponse(BaseModel):
    """Response indicating whether current user follows another user."""

    is_following: bool
