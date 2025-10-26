"""Pydantic models for activity feed."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class ActivityType(str, Enum):
    """Types of activities that can appear in the feed."""

    SPOT_CREATED = "spot_created"
    SPOT_RATED = "spot_rated"
    SPOT_COMMENTED = "spot_commented"
    SPOT_FAVORITED = "spot_favorited"
    SPOT_CHECKED_IN = "spot_checked_in"
    SESSION_CREATED = "session_created"
    SESSION_RSVP = "session_rsvp"


class TargetType(str, Enum):
    """Types of entities that can be targets of activities."""

    SPOT = "spot"
    RATING = "rating"
    COMMENT = "comment"
    FAVORITE = "favorite"
    CHECK_IN = "check_in"
    SESSION = "session"
    RSVP = "rsvp"


class ActivityActor(BaseModel):
    """Simplified user model for activity actor."""

    id: UUID
    username: str
    display_name: str | None = None
    profile_photo_url: str | None = None

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class ActivityBase(BaseModel):
    """Base model for activity data."""

    activity_type: ActivityType
    target_type: TargetType
    target_id: str


class ActivityCreate(ActivityBase):
    """Model for creating a new activity."""

    metadata: dict | None = Field(None, description="Optional metadata for the activity")


class Activity(ActivityBase):
    """Complete activity model."""

    id: UUID
    user_id: UUID
    actor: ActivityActor | None = None
    metadata: dict | None = None
    created_at: datetime

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class ActivityFeedResponse(BaseModel):
    """Response containing a list of activities with pagination."""

    activities: list[Activity]
    total: int
    limit: int
    offset: int
    has_more: bool = Field(description="Whether there are more activities to load")


class ActivitySummary(BaseModel):
    """Summary of an activity for quick display."""

    id: UUID
    activity_type: ActivityType
    actor_username: str
    created_at: datetime
    message: str = Field(description="Human-readable summary of the activity")


class ActivityDetails(BaseModel):
    """Detailed activity with enriched information."""

    activity: Activity
    target_details: dict | None = Field(None, description="Details about the target entity")
