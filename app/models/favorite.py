"""Pydantic models for user favorite skate spots."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class Favorite(BaseModel):
    """A favorite relationship between a user and a skate spot."""

    user_id: UUID = Field(..., description="Identifier of the user who favorited the spot.")
    spot_id: UUID = Field(..., description="Identifier of the favorited skate spot.")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the favorite was created.",
    )


class FavoriteStatus(BaseModel):
    """Response payload indicating whether a spot is favorited by the user."""

    spot_id: UUID = Field(..., description="Identifier of the skate spot.")
    is_favorite: bool = Field(..., description="Whether the spot is currently favorited.")
