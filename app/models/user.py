"""Pydantic models for user data."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserBase(BaseModel):
    """Base user model with common attributes."""

    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)


class UserCreate(UserBase):
    """Model for creating a new user."""

    password: str = Field(..., min_length=8, max_length=100)


class UserLogin(BaseModel):
    """Model for user login."""

    username: str
    password: str


class UserUpdate(BaseModel):
    """Model for updating user profile."""

    bio: str | None = Field(None, max_length=500)
    avatar_url: str | None = Field(None, max_length=500)
    location: str | None = Field(None, max_length=100)


class User(UserBase):
    """Model representing a user (returned in responses)."""

    id: UUID
    display_name: str | None = None
    bio: str | None = None
    location: str | None = None
    website_url: str | None = None
    instagram_handle: str | None = None
    profile_photo_url: str | None = None
    is_active: bool
    is_admin: bool
    bio: str | None = None
    avatar_url: str | None = None
    location: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class UserPublicProfile(BaseModel):
    """Public view of a user profile (without email)."""

    id: UUID
    username: str
    bio: str | None = None
    avatar_url: str | None = None
    location: str | None = None
    created_at: datetime

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class UserStats(BaseModel):
    """User statistics for profile display."""

    spots_count: int = 0
    photos_count: int = 0
    comments_count: int = 0
    ratings_count: int = 0
    favorites_count: int = 0


class UserProfileWithStats(UserPublicProfile):
    """User profile with activity statistics."""

    stats: UserStats


class Token(BaseModel):
    """Model for authentication token response."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Model for decoded token data."""

    user_id: str | None = None
    username: str | None = None


class UserProfileUpdate(BaseModel):
    """Model representing editable profile fields for a user."""

    display_name: str | None = Field(default=None, max_length=100)
    bio: str | None = Field(default=None, max_length=500)
    location: str | None = Field(default=None, max_length=100)
    website_url: str | None = Field(default=None, max_length=255)
    instagram_handle: str | None = Field(default=None, max_length=100)
    profile_photo_url: str | None = Field(default=None, max_length=512)

    @field_validator(
        "display_name",
        "bio",
        "location",
        "website_url",
        "instagram_handle",
        "profile_photo_url",
        mode="before",
    )
    @classmethod
    def _blank_to_none(cls, value: str | None) -> str | None:
        """Convert blank strings submitted via forms into ``None``."""

        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value
