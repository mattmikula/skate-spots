"""Pydantic models describing public user profile data."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel

# TC001 suppressed: Pydantic requires this import at runtime for model validation
from app.models.checkin import CheckinSummary  # noqa: TC001


class UserProfileStats(BaseModel):
    """Aggregate counts for a user's contributions."""

    spots_added: int
    photos_uploaded: int
    comments_posted: int
    ratings_left: int
    checkins_count: int = 0
    average_rating_given: float | None = None


class UserSpotSummary(BaseModel):
    """A lightweight summary of a skate spot owned by a user."""

    id: UUID
    name: str
    city: str
    country: str
    created_at: datetime
    photo_count: int
    average_rating: float | None = None
    ratings_count: int = 0


class UserCommentSummary(BaseModel):
    """Representation of a recent comment left by the user."""

    id: UUID
    spot_id: UUID
    spot_name: str
    content: str
    created_at: datetime


class UserRatingSummary(BaseModel):
    """Representation of a recent rating left by the user."""

    id: UUID
    spot_id: UUID
    spot_name: str
    score: int
    comment: str | None = None
    created_at: datetime


class UserActivityType(str, Enum):
    """Types of activity displayed in the profile feed."""

    SPOT_CREATED = "spot_created"
    COMMENTED = "commented"
    RATED = "rated"
    PHOTO_UPLOADED = "photo_uploaded"
    CHECKED_IN = "checked_in"


class UserActivityItem(BaseModel):
    """Activity feed entry summarising recent user actions."""

    type: UserActivityType
    created_at: datetime
    spot_id: UUID | None = None
    spot_name: str | None = None
    comment: str | None = None
    rating_score: int | None = None
    photo_path: str | None = None


class UserProfile(BaseModel):
    """Public profile information combined with recent activity."""

    id: UUID
    username: str
    display_name: str | None = None
    bio: str | None = None
    location: str | None = None
    website_url: str | None = None
    instagram_handle: str | None = None
    profile_photo_url: str | None = None
    joined_at: datetime
    stats: UserProfileStats
    spots: list[UserSpotSummary]
    recent_comments: list[UserCommentSummary]
    recent_ratings: list[UserRatingSummary]
    recent_checkins: list[CheckinSummary] | None = None
    activity: list[UserActivityItem]
