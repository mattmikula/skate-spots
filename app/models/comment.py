"""Pydantic models for skate spot comments."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class CommentBase(BaseModel):
    """Shared fields for skate spot comments."""

    content: str = Field(..., min_length=1, max_length=1000)

    @field_validator("content")
    @classmethod
    def _strip_content(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Comment content cannot be empty.")
        return stripped


class CommentCreate(CommentBase):
    """Payload for creating a new comment."""

    pass


class CommentAuthor(BaseModel):
    """Public information about the author of a comment."""

    id: UUID
    username: str = Field(..., min_length=1, max_length=50)


class Comment(CommentBase):
    """Representation of a persisted comment."""

    id: UUID
    spot_id: UUID
    user_id: UUID
    author: CommentAuthor
    created_at: datetime
    updated_at: datetime
    spot_name: str | None = None  # Optional field for profile/listing contexts

    class Config:
        """Enable ORM mode for compatibility with SQLAlchemy objects."""

        from_attributes = True
