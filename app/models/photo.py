"""Pydantic models for skate spot photos."""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class SpotPhotoBase(BaseModel):
    """Base model for spot photo data."""

    caption: str | None = Field(
        None,
        max_length=500,
        description="Optional caption or description of the photo",
    )
    is_primary: bool = Field(
        False,
        description="Whether this is the primary/featured photo for the spot",
    )


class SpotPhotoCreate(SpotPhotoBase):
    """Model for creating a new spot photo."""

    pass


class SpotPhoto(SpotPhotoBase):
    """Complete spot photo model with database fields."""

    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    spot_id: UUID = Field(..., description="ID of the associated skate spot")
    user_id: str = Field(..., description="ID of the user who uploaded the photo")
    filename: str = Field(..., description="Original filename of the uploaded photo")
    file_path: str = Field(
        ...,
        description="Relative path to the stored photo (relative to static/uploads/photos/)",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the photo was uploaded",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "spot_id": "223e4567-e89b-12d3-a456-426614174001",
                "user_id": "user-123",
                "filename": "downtown_rails.jpg",
                "file_path": "2024-10/123e4567/downtown_rails.jpg",
                "caption": "Great transition spot with smooth concrete",
                "is_primary": True,
                "created_at": "2024-10-18T12:00:00Z",
            }
        }
    }


class PhotoUploadResponse(BaseModel):
    """Response model for successful photo upload."""

    photo: SpotPhoto = Field(..., description="The created photo object")
    message: str = Field(..., description="Success message")
