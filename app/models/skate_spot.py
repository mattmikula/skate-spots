"""Pydantic models for skate spots."""

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class SpotType(str, Enum):
    """Types of skate spots."""

    STREET = "street"
    PARK = "park"
    BOWL = "bowl"
    VERT = "vert"
    MINI_RAMP = "mini_ramp"
    STAIRS = "stairs"
    RAIL = "rail"
    LEDGE = "ledge"
    GAP = "gap"
    OTHER = "other"


class Difficulty(str, Enum):
    """Difficulty levels for skate spots."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class Location(BaseModel):
    """Geographic location of a skate spot."""

    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    address: str | None = Field(None, description="Human-readable address")
    city: str = Field(..., min_length=1, description="City name")
    country: str = Field(..., min_length=1, description="Country name")


class SkateSpotBase(BaseModel):
    """Base model for skate spot data."""

    name: str = Field(..., min_length=1, max_length=100, description="Name of the skate spot")
    description: str = Field(..., min_length=1, max_length=1000, description="Detailed description")
    spot_type: SpotType = Field(..., description="Type of skate spot")
    difficulty: Difficulty = Field(..., description="Difficulty level")
    location: Location = Field(..., description="Geographic location")
    is_public: bool = Field(True, description="Whether the spot is publicly accessible")
    requires_permission: bool = Field(False, description="Whether permission is needed to skate")


class SkateSpotCreate(SkateSpotBase):
    """Model for creating a new skate spot."""

    pass


class SkateSpotUpdate(BaseModel):
    """Model for updating an existing skate spot."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, min_length=1, max_length=1000)
    spot_type: SpotType | None = None
    difficulty: Difficulty | None = None
    location: Location | None = None
    is_public: bool | None = None
    requires_permission: bool | None = None


class SkateSpot(SkateSpotBase):
    """Complete skate spot model with database fields."""

    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Downtown Rails",
                "description": "Great set of rails perfect for grinding practice",
                "spot_type": "rail",
                "difficulty": "intermediate",
                "location": {
                    "latitude": 40.7128,
                    "longitude": -74.0060,
                    "address": "123 Main St",
                    "city": "New York",
                    "country": "USA",
                },
                "is_public": True,
                "requires_permission": False,
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z",
            }
        }
    }
