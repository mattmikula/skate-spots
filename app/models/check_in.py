"""Pydantic models for spot check-ins."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.activity import ActivityActor  # noqa: TCH001


class SpotCheckInStatus(str, Enum):
    """Allowable statuses for a spot check-in."""

    HEADING = "heading"
    ARRIVED = "arrived"


class SpotCheckInBase(BaseModel):
    """Shared fields for creating or updating a check-in."""

    status: SpotCheckInStatus = Field(description="Current state of the skater.")
    message: str | None = Field(
        default=None,
        max_length=280,
        description="Optional short note visible to other skaters.",
    )


class SpotCheckInCreate(SpotCheckInBase):
    """Payload for creating a new check-in."""

    ttl_minutes: int | None = Field(
        default=None,
        ge=15,
        le=240,
        description="Optional custom expiration window in minutes (default 120).",
    )


class SpotCheckInUpdate(BaseModel):
    """Payload for updating an existing check-in."""

    status: SpotCheckInStatus | None = Field(default=None, description="Updated status.")
    message: str | None = Field(
        default=None,
        max_length=280,
        description="Updated note for the check-in.",
    )
    renew_minutes: int | None = Field(
        default=None,
        ge=15,
        le=240,
        description="Extend the active window for this check-in.",
    )


class SpotCheckOut(BaseModel):
    """Payload for ending a check-in."""

    message: str | None = Field(
        default=None,
        max_length=280,
        description="Optional wrap-up note when checking out.",
    )


class SpotCheckIn(BaseModel):
    """Representation of a spot check-in."""

    id: UUID
    spot_id: UUID
    user_id: UUID
    status: SpotCheckInStatus
    message: str | None
    expires_at: datetime
    ended_at: datetime | None
    created_at: datetime
    updated_at: datetime
    is_active: bool = Field(description="True if the check-in is still active.")
    actor: ActivityActor = Field(description="User information for display.")

    class Config:
        """Enable ORM mode."""

        from_attributes = True
