"""Pydantic models for spot check-ins and session logging."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CheckinCreate(BaseModel):
    """Request model for creating a new check-in."""

    notes: str | None = Field(None, max_length=500)


class Checkin(BaseModel):
    """Complete check-in record."""

    id: UUID
    spot_id: UUID
    user_id: str
    notes: str | None = None
    checked_in_at: datetime

    model_config = {"from_attributes": True}


class CheckinStats(BaseModel):
    """Aggregated check-in statistics for a spot."""

    today_count: int = 0
    week_count: int = 0
    total_count: int = 0
    user_checked_in_today: bool = False


class CheckinSummary(BaseModel):
    """Summary of a check-in for user profile/activity feed."""

    id: UUID
    spot_id: UUID
    spot_name: str
    checked_in_at: datetime
    notes: str | None = None

    model_config = {"from_attributes": True}
