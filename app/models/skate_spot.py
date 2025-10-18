"""Pydantic models for skate spots."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, computed_field, field_validator

from app.core.config import get_settings


class SpotType(str, Enum):
    """Types of skate spots."""

    STREET = "street"
    PARK = "park"
    SKATEPARK = "skatepark"
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


class SpotPhotoBase(BaseModel):
    """Shared fields for skate spot photos stored on disk."""

    path: str = Field(
        ...,
        min_length=1,
        description="Relative path to the photo within the media directory",
    )
    original_filename: str | None = Field(
        None, description="Original filename supplied by the uploader"
    )


class SpotPhotoCreate(SpotPhotoBase):
    """Payload for creating a new skate spot photo."""

    pass


class SpotPhoto(SpotPhotoBase):
    """Representation of a stored skate spot photo."""

    id: UUID = Field(default_factory=uuid4, description="Unique identifier for the photo")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp when the photo was added"
    )

    @computed_field(return_type=str)
    def url(self) -> str:
        """Build the public URL for the stored photo based on application settings."""

        settings = get_settings()
        base = settings.media_url_path.rstrip("/") or "/media"
        relative = self.path.lstrip("/")
        return f"{base}/{relative}" if relative else base


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

    photos: list[SpotPhotoCreate] = Field(
        default_factory=list,
        description="Optional collection of photos to associate with the new spot",
    )


class SkateSpotUpdate(BaseModel):
    """Model for updating an existing skate spot."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, min_length=1, max_length=1000)
    spot_type: SpotType | None = None
    difficulty: Difficulty | None = None
    location: Location | None = None
    is_public: bool | None = None
    requires_permission: bool | None = None
    photos: list[SpotPhotoCreate] | None = Field(
        default=None,
        description=(
            "Optional replacement list of photos. ``None`` leaves photos unchanged, an empty"
            " list removes all existing photos."
        ),
    )


class SkateSpotFilters(BaseModel):
    """Query parameters that can be used to filter skate spots."""

    search: str | None = Field(
        default=None,
        description="Search term applied to name, description, city, and country",
    )
    spot_types: list[SpotType] | None = Field(default=None, description="Allowed spot types")
    difficulties: list[Difficulty] | None = Field(
        default=None, description="Allowed difficulty levels"
    )
    city: str | None = Field(default=None, description="Filter by city (case-insensitive)")
    country: str | None = Field(default=None, description="Filter by country (case-insensitive)")
    is_public: bool | None = Field(
        default=None, description="Whether the spot must be publicly accessible"
    )
    requires_permission: bool | None = Field(
        default=None, description="Whether the spot requires permission"
    )

    @field_validator("search", "city", "country", mode="before")
    @classmethod
    def _strip_blank_strings(cls, value: str | None) -> str | None:
        """Normalise blank strings into ``None`` for easier downstream checks."""

        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value

    def has_filters(self) -> bool:
        """Return ``True`` when at least one filter value has been provided."""

        for value in self.model_dump().values():
            if isinstance(value, list):
                if value:
                    return True
            elif value is not None:
                return True
        return False


class SkateSpot(SkateSpotBase):
    """Complete skate spot model with database fields."""

    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )
    average_rating: float | None = Field(
        None,
        ge=1,
        le=5,
        description="Average user rating between 1 and 5, if the spot has been rated.",
    )
    ratings_count: int = Field(
        0,
        ge=0,
        description="Total number of ratings submitted for this skate spot.",
    )
    photos: list[SpotPhoto] = Field(
        default_factory=list,
        description="Photos that showcase the skate spot.",
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
                "average_rating": 4.5,
                "ratings_count": 12,
                "photos": [
                    {
                        "id": "223e4567-e89b-12d3-a456-426614174111",
                        "path": "2024/05/downtown-rails-1.jpg",
                        "url": "/media/2024/05/downtown-rails-1.jpg",
                        "original_filename": "downtown-rails-1.jpg",
                        "created_at": "2023-01-01T00:00:00Z",
                    }
                ],
            }
        }
    }


class GeoJSONPoint(BaseModel):
    """GeoJSON Point geometry."""

    type: str = Field(default="Point", description="Geometry type")
    coordinates: tuple[float, float] = Field(
        ..., description="Coordinates as [longitude, latitude]"
    )


class GeoJSONFeatureProperties(BaseModel):
    """Properties for a GeoJSON feature representing a skate spot."""

    id: str = Field(..., description="Unique identifier as string")
    name: str = Field(..., description="Name of the skate spot")
    description: str = Field(..., description="Detailed description")
    spot_type: str = Field(..., description="Type of skate spot")
    difficulty: str = Field(..., description="Difficulty level")
    city: str = Field(..., description="City name")
    country: str = Field(..., description="Country name")
    address: str | None = Field(None, description="Human-readable address")
    is_public: bool = Field(..., description="Whether the spot is publicly accessible")
    requires_permission: bool = Field(..., description="Whether permission is needed to skate")


class GeoJSONFeature(BaseModel):
    """A GeoJSON Feature representing a skate spot."""

    type: str = Field(default="Feature", description="Feature type")
    geometry: GeoJSONPoint = Field(..., description="Point geometry")
    properties: GeoJSONFeatureProperties = Field(..., description="Feature properties")


class GeoJSONFeatureCollection(BaseModel):
    """A GeoJSON FeatureCollection of skate spots."""

    type: str = Field(default="FeatureCollection", description="Collection type")
    features: list[GeoJSONFeature] = Field(..., description="List of features")

    model_config = {
        "json_schema_extra": {
            "example": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [-74.0060, 40.7128],
                        },
                        "properties": {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "name": "Downtown Rails",
                            "description": "Great rails for grinding",
                            "spot_type": "rail",
                            "difficulty": "intermediate",
                            "city": "New York",
                            "country": "USA",
                            "address": "123 Main St",
                            "is_public": True,
                            "requires_permission": False,
                        },
                    }
                ],
            }
        }
    }
