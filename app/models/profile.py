"""Pydantic models for user profiles."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from app.models.comment import Comment  # noqa: TC001
    from app.models.rating import Rating  # noqa: TC001
    from app.models.skate_spot import SkateSpot  # noqa: TC001


class UserStatistics(BaseModel):
    """Statistics for a user's activity."""

    spots_added: int = Field(..., ge=0, description="Total number of skate spots added by the user")
    photos_uploaded: int = Field(
        ..., ge=0, description="Total number of photos uploaded by the user"
    )
    comments_posted: int = Field(
        ..., ge=0, description="Total number of comments posted by the user"
    )
    ratings_given: int = Field(..., ge=0, description="Total number of ratings given by the user")

    model_config = {
        "json_schema_extra": {
            "example": {
                "spots_added": 5,
                "photos_uploaded": 12,
                "comments_posted": 8,
                "ratings_given": 15,
            }
        }
    }


class ActivityType(str, Enum):
    """Types of user activities."""

    SPOT_CREATED = "spot_created"
    SPOT_UPDATED = "spot_updated"
    PHOTO_UPLOADED = "photo_uploaded"
    COMMENT_POSTED = "comment_posted"
    RATING_GIVEN = "rating_given"


class ActivityItem(BaseModel):
    """A single activity in the user's feed."""

    activity_type: ActivityType = Field(..., description="Type of activity")
    timestamp: datetime = Field(..., description="When the activity occurred")
    spot_id: UUID = Field(..., description="ID of the related skate spot")
    spot_name: str = Field(..., description="Name of the skate spot")
    details: str | None = Field(None, description="Additional details about the activity")

    model_config = {
        "json_schema_extra": {
            "example": {
                "activity_type": "spot_created",
                "timestamp": "2025-10-20T12:00:00Z",
                "spot_id": "123e4567-e89b-12d3-a456-426614174000",
                "spot_name": "Downtown Ledge",
                "details": "Added a new street spot",
            }
        }
    }


class UserActivity(BaseModel):
    """Collection of user activities."""

    activities: list[ActivityItem] = Field(
        default_factory=list, description="List of recent user activities"
    )


class PublicUserInfo(BaseModel):
    """Public information about a user for their profile page."""

    id: UUID = Field(..., description="Unique identifier for the user")
    username: str = Field(..., description="Username")
    created_at: datetime = Field(..., description="When the user joined")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "username": "skater_dude",
                "created_at": "2025-01-15T10:30:00Z",
            }
        },
    }


class UserProfile(BaseModel):
    """Complete user profile with statistics and activity."""

    user: PublicUserInfo = Field(..., description="Public user information")
    statistics: UserStatistics = Field(..., description="User activity statistics")
    recent_spots: list[SkateSpot] = Field(
        default_factory=list, description="Recently added skate spots"
    )
    recent_comments: list[Comment] = Field(
        default_factory=list, description="Recently posted comments"
    )
    recent_ratings: list[Rating] = Field(
        default_factory=list, description="Recently given ratings"
    )
    activity: UserActivity = Field(default_factory=UserActivity, description="Recent activity feed")

    model_config = {"from_attributes": True}
