"""Pydantic models for skate spot ratings."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class RatingBase(BaseModel):
    """Base model for rating data."""

    score: int = Field(
        ...,
        ge=1,
        le=5,
        description="User-provided rating score between 1 (worst) and 5 (best).",
    )
    comment: str | None = Field(
        None,
        max_length=500,
        description="Optional short comment describing the rating.",
    )


class RatingCreate(RatingBase):
    """Model for creating a new rating."""

    pass


class RatingUpdate(BaseModel):
    """Model for updating an existing rating."""

    score: int | None = Field(
        None,
        ge=1,
        le=5,
        description="Updated rating score between 1 and 5.",
    )
    comment: str | None = Field(
        None,
        max_length=500,
        description="Updated optional comment for the rating.",
    )


class Rating(RatingBase):
    """Model representing a persisted rating."""

    id: UUID = Field(default_factory=uuid4, description="Unique identifier for the rating.")
    user_id: UUID = Field(..., description="Identifier of the user who created the rating.")
    spot_id: UUID = Field(..., description="Identifier of the skate spot being rated.")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when the rating was created.",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when the rating was last updated.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "2bf90e3a-a7fb-4e40-aaf6-70c82e28aa1a",
                "user_id": "55ee02fe-5063-4fe0-84e8-ecbe40a3b601",
                "spot_id": "9f5eb474-b7c0-4b1f-8dc1-61bf7fecee64",
                "score": 4,
                "comment": "Great flow and clean lines.",
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-02T12:30:00Z",
            }
        }
    }


class RatingSummary(BaseModel):
    """Aggregated rating information for a skate spot."""

    average_score: float | None = Field(
        None,
        description="Average rating score for the spot rounded to two decimals, if rated.",
    )
    ratings_count: int = Field(
        0,
        ge=0,
        description="Total number of ratings recorded for the spot.",
    )


class RatingSummaryResponse(RatingSummary):
    """Rating summary enriched with the current user's rating when available."""

    user_rating: Rating | None = Field(
        None,
        description="The authenticated user's rating for the spot, if it exists.",
    )
