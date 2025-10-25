"""Pydantic models for user notifications."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.activity import ActivityActor, ActivityType


class NotificationType(str, Enum):
    """Supported notification categories."""

    SPOT_CREATED = ActivityType.SPOT_CREATED.value
    SPOT_RATED = ActivityType.SPOT_RATED.value
    SPOT_COMMENTED = ActivityType.SPOT_COMMENTED.value
    SPOT_FAVORITED = ActivityType.SPOT_FAVORITED.value
    SESSION_CREATED = ActivityType.SESSION_CREATED.value
    SESSION_RSVP = ActivityType.SESSION_RSVP.value


class Notification(BaseModel):
    """Notification returned to clients."""

    id: UUID
    notification_type: NotificationType
    activity_id: UUID | None = Field(default=None, description="Related activity feed entry.")
    message: str = Field(description="Human-friendly summary.")
    metadata: dict | None = Field(default=None, description="Additional context metadata.")
    is_read: bool = Field(default=False, description="Has the recipient read the notification?")
    created_at: datetime
    read_at: datetime | None = Field(default=None, description="Timestamp when read.")
    actor: ActivityActor | None = Field(
        default=None,
        description="User that triggered the notification when applicable.",
    )

    class Config:
        """Enable ORM mode."""

        from_attributes = True


class NotificationListResponse(BaseModel):
    """Paginated notification response."""

    notifications: list[Notification]
    total: int
    unread_count: int
    limit: int
    offset: int
    has_more: bool


class NotificationUnreadCount(BaseModel):
    """Payload for unread count."""

    unread_count: int


class NotificationBulkUpdateResult(BaseModel):
    """Result payload for bulk read operations."""

    updated: int
    unread_count: int
