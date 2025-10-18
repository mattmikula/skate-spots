"""Pydantic models for user favourite skate spots."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class Favorite(BaseModel):
    """A favourite relationship between a user and a skate spot."""

    user_id: UUID = Field(..., description="Identifier of the user who favourited the spot.")
    spot_id: UUID = Field(..., description="Identifier of the favourited skate spot.")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the favourite was created.",
    )


class FavoriteStatus(BaseModel):
    """Response payload indicating whether a spot is favourited by the user."""

    spot_id: UUID = Field(..., description="Identifier of the skate spot.")
    is_favorite: bool = Field(..., description="Whether the spot is currently favourited.")
