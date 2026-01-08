"""Pydantic models for spot condition reports."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.activity import ActivityActor  # noqa: TCH001


class ConditionSurfaceQuality(str, Enum):
    """Surface quality ratings for skate spots."""

    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    TERRIBLE = "terrible"


class ConditionCrowdedness(str, Enum):
    """Crowdedness levels for skate spots."""

    EMPTY = "empty"
    QUIET = "quiet"
    MODERATE = "moderate"
    BUSY = "busy"
    PACKED = "packed"


class ConditionSecurity(str, Enum):
    """Security/harassment levels for skate spots."""

    CLEAR = "clear"
    RELAXED = "relaxed"
    WATCHFUL = "watchful"
    STRICT = "strict"
    HOSTILE = "hostile"


class ConditionOverallStatus(str, Enum):
    """Overall spot condition status."""

    PRIME = "prime"
    GOOD = "good"
    OKAY = "okay"
    ROUGH = "rough"
    CLOSED = "closed"


class SpotConditionReportCreate(BaseModel):
    """Payload for creating a condition report."""

    surface_quality: ConditionSurfaceQuality | None = Field(
        default=None, description="Surface condition rating"
    )
    crowdedness: ConditionCrowdedness | None = Field(
        default=None, description="How crowded the spot is"
    )
    security: ConditionSecurity | None = Field(
        default=None, description="Security/harassment level"
    )
    overall_status: ConditionOverallStatus = Field(description="Overall spot condition")
    note: str | None = Field(
        default=None, max_length=280, description="Optional note about conditions"
    )


class SpotConditionReport(BaseModel):
    """Full condition report response."""

    id: UUID
    spot_id: UUID
    user_id: UUID
    surface_quality: ConditionSurfaceQuality | None
    crowdedness: ConditionCrowdedness | None
    security: ConditionSecurity | None
    overall_status: ConditionOverallStatus
    note: str | None
    expires_at: datetime
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime
    is_active: bool = Field(description="Whether report is still valid (not expired or deleted)")
    reporter: ActivityActor = Field(description="User who filed the report")

    class Config:
        """Pydantic configuration."""

        from_attributes = True
