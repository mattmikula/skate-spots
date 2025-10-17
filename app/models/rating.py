"""Pydantic models for ratings."""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class RatingBase(BaseModel):
    """Base model for rating data."""

    score: int = Field(..., ge=1, le=5, description="Rating score from 1 to 5 stars")
    review: str | None = Field(None, max_length=500, description="Optional review text")


class RatingCreate(RatingBase):
    """Model for creating a new rating."""

    pass


class RatingUpdate(BaseModel):
    """Model for updating an existing rating."""

    score: int | None = Field(None, ge=1, le=5, description="Rating score from 1 to 5 stars")
    review: str | None = Field(None, max_length=500, description="Optional review text")


class Rating(RatingBase):
    """Complete rating model with database fields."""

    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    spot_id: UUID = Field(..., description="ID of the rated skate spot")
    user_id: UUID = Field(..., description="ID of the user who created the rating")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "spot_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "660e8400-e29b-41d4-a716-446655440000",
                "score": 5,
                "review": "Amazing spot! Great for learning new tricks.",
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z",
            }
        }
    }


class RatingStats(BaseModel):
    """Statistics about ratings for a skate spot."""

    average_score: float = Field(..., ge=0, le=5, description="Average rating score")
    total_ratings: int = Field(..., ge=0, description="Total number of ratings")
    distribution: dict[int, int] = Field(..., description="Distribution of ratings by score (1-5)")
