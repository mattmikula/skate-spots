"""Pydantic models for user data."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


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
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class Token(BaseModel):
    """Model for authentication token response."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Model for decoded token data."""

    user_id: str | None = None
    username: str | None = None
