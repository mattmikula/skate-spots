"""Pydantic models for skate session scheduling."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, computed_field, field_validator, model_validator


class SessionStatus(str, Enum):
    """Lifecycle states for an organised session."""

    SCHEDULED = "scheduled"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class SessionResponse(str, Enum):
    """Types of RSVP responses for a session."""

    GOING = "going"
    MAYBE = "maybe"
    WAITLIST = "waitlist"


class SessionBase(BaseModel):
    """Shared fields for creating or updating a session."""

    title: str = Field(..., min_length=1, max_length=120)
    description: str | None = Field(
        default=None,
        max_length=2000,
        description="Optional description with plans for the meetup.",
    )
    start_time: datetime
    end_time: datetime
    meet_location: str | None = Field(default=None, max_length=255)
    skill_level: str | None = Field(default=None, max_length=50)
    capacity: int | None = Field(default=None, ge=1)

    @field_validator("title")
    @classmethod
    def _normalise_title(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Title cannot be blank.")
        return stripped

    @field_validator("description", "meet_location", "skill_level", mode="before")
    @classmethod
    def _strip_optional(cls, value: str | None) -> str | None:
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value

    @model_validator(mode="after")
    def _validate_times(self) -> SessionBase:
        if self.end_time <= self.start_time:
            raise ValueError("End time must be after the start time.")
        return self


class SessionCreate(SessionBase):
    """Payload for creating a new session."""

    pass


class SessionUpdate(BaseModel):
    """Payload for updating an existing session."""

    title: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    start_time: datetime | None = None
    end_time: datetime | None = None
    meet_location: str | None = Field(default=None, max_length=255)
    skill_level: str | None = Field(default=None, max_length=50)
    capacity: int | None = Field(default=None, ge=1)
    status: SessionStatus | None = None

    @field_validator("title")
    @classmethod
    def _normalise_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("Title cannot be blank.")
        return stripped

    @field_validator("description", "meet_location", "skill_level", mode="before")
    @classmethod
    def _strip_optional(cls, value: str | None) -> str | None:
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value

    @model_validator(mode="after")
    def _validate_times(self) -> SessionUpdate:
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValueError("End time must be after the start time.")
        return self


class SessionStats(BaseModel):
    """Aggregated RSVP counts for a session."""

    going: int = 0
    maybe: int = 0
    waitlist: int = 0


class Session(SessionBase):
    """Representation of a stored session."""

    id: UUID = Field(default_factory=uuid4)
    spot_id: UUID
    organizer_id: UUID
    organizer_username: str | None = None
    status: SessionStatus = SessionStatus.SCHEDULED
    created_at: datetime
    updated_at: datetime
    stats: SessionStats = Field(default_factory=SessionStats)
    user_response: SessionResponse | None = None

    @computed_field(return_type=int | None)
    def spots_remaining(self) -> int | None:
        if self.capacity is None:
            return None
        remaining = self.capacity - self.stats.going
        return remaining if remaining >= 0 else 0

    @computed_field(return_type=bool)
    def is_full(self) -> bool:
        if self.capacity is None:
            return False
        return self.stats.going >= self.capacity


class SessionRSVPBase(BaseModel):
    """Shared fields for RSVP operations."""

    response: SessionResponse = SessionResponse.GOING
    note: str | None = Field(default=None, max_length=300)

    @field_validator("note", mode="before")
    @classmethod
    def _strip_note(cls, value: str | None) -> str | None:
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value


class SessionRSVPCreate(SessionRSVPBase):
    """Payload for creating or updating an RSVP."""

    pass


class SessionRSVP(SessionRSVPBase):
    """Representation of a stored RSVP."""

    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
