"""SQLAlchemy ORM models for the application."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class UserORM(Base):
    """Database model representing a user."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    bio: Mapped[str | None] = mapped_column(String(500), nullable=True)
    location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    website_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    instagram_handle: Mapped[str | None] = mapped_column(String(100), nullable=True)
    profile_photo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    skate_spots: Mapped[list[SkateSpotORM]] = relationship(
        "SkateSpotORM", back_populates="owner", cascade="all, delete-orphan"
    )
    ratings: Mapped[list[RatingORM]] = relationship(
        "RatingORM", back_populates="user", cascade="all, delete-orphan"
    )
    favorite_spots: Mapped[list[FavoriteSpotORM]] = relationship(
        "FavoriteSpotORM",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    hosted_sessions: Mapped[list[SessionORM]] = relationship(
        "SessionORM",
        back_populates="organizer",
        cascade="all, delete-orphan",
    )
    session_rsvps: Mapped[list[SessionRSVPORM]] = relationship(
        "SessionRSVPORM",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    uploaded_photos: Mapped[list[SpotPhotoORM]] = relationship(
        "SpotPhotoORM",
        back_populates="uploader",
        cascade="all, delete-orphan",
    )
    comments: Mapped[list[SpotCommentORM]] = relationship(
        "SpotCommentORM",
        back_populates="author",
        cascade="all, delete-orphan",
    )
    followers: Mapped[list[UserFollowORM]] = relationship(
        "UserFollowORM",
        foreign_keys="UserFollowORM.following_id",
        back_populates="following_user",
        cascade="all, delete-orphan",
    )
    following: Mapped[list[UserFollowORM]] = relationship(
        "UserFollowORM",
        foreign_keys="UserFollowORM.follower_id",
        back_populates="follower_user",
        cascade="all, delete-orphan",
    )
    activities: Mapped[list[ActivityFeedORM]] = relationship(
        "ActivityFeedORM",
        back_populates="actor",
        cascade="all, delete-orphan",
    )
    notifications: Mapped[list[NotificationORM]] = relationship(
        "NotificationORM",
        back_populates="user",
        foreign_keys="NotificationORM.user_id",
        cascade="all, delete-orphan",
    )
    check_ins: Mapped[list[SpotCheckInORM]] = relationship(
        "SpotCheckInORM",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class SkateSpotORM(Base):
    """Database model representing a skate spot."""

    __tablename__ = "skate_spots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=False)
    spot_type: Mapped[str] = mapped_column(String(50), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(50), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    requires_permission: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    owner: Mapped[UserORM] = relationship("UserORM", back_populates="skate_spots")
    ratings: Mapped[list[RatingORM]] = relationship(
        "RatingORM", back_populates="spot", cascade="all, delete-orphan"
    )
    favorited_by: Mapped[list[FavoriteSpotORM]] = relationship(
        "FavoriteSpotORM",
        back_populates="spot",
        cascade="all, delete-orphan",
    )
    photos: Mapped[list[SpotPhotoORM]] = relationship(
        "SpotPhotoORM",
        back_populates="spot",
        cascade="all, delete-orphan",
    )
    sessions: Mapped[list[SessionORM]] = relationship(
        "SessionORM",
        back_populates="spot",
        cascade="all, delete-orphan",
    )
    comments: Mapped[list[SpotCommentORM]] = relationship(
        "SpotCommentORM",
        back_populates="spot",
        cascade="all, delete-orphan",
    )
    check_ins: Mapped[list[SpotCheckInORM]] = relationship(
        "SpotCheckInORM",
        back_populates="spot",
        cascade="all, delete-orphan",
    )
    weather_snapshot: Mapped[WeatherSnapshotORM | None] = relationship(
        "WeatherSnapshotORM",
        back_populates="spot",
        cascade="all, delete-orphan",
        uselist=False,
    )


class SpotPhotoORM(Base):
    """Database model representing a photo attached to a skate spot."""

    __tablename__ = "spot_photos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    spot_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("skate_spots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    uploader_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(UTC)
    )

    spot: Mapped[SkateSpotORM] = relationship("SkateSpotORM", back_populates="photos")
    uploader: Mapped[UserORM | None] = relationship("UserORM", back_populates="uploaded_photos")


class RatingORM(Base):
    """Database model representing a user rating for a skate spot."""

    __tablename__ = "spot_ratings"
    __table_args__ = (
        UniqueConstraint("spot_id", "user_id", name="uq_spot_ratings_user_spot"),
        CheckConstraint("score BETWEEN 1 AND 5", name="ck_spot_ratings_score_range"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    spot_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("skate_spots.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    spot: Mapped[SkateSpotORM] = relationship("SkateSpotORM", back_populates="ratings")
    user: Mapped[UserORM] = relationship("UserORM", back_populates="ratings")


class FavoriteSpotORM(Base):
    """Association table linking users to their favorite skate spots."""

    __tablename__ = "favorite_spots"
    __table_args__ = (UniqueConstraint("user_id", "spot_id", name="uq_favorite_user_spot"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    spot_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("skate_spots.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(UTC)
    )

    user: Mapped[UserORM] = relationship("UserORM", back_populates="favorite_spots")
    spot: Mapped[SkateSpotORM] = relationship("SkateSpotORM", back_populates="favorited_by")


class SpotCommentORM(Base):
    """Database model representing a comment left on a skate spot."""

    __tablename__ = "spot_comments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    spot_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("skate_spots.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(String(1000), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    spot: Mapped[SkateSpotORM] = relationship("SkateSpotORM", back_populates="comments")
    author: Mapped[UserORM] = relationship("UserORM", back_populates="comments")


class UserFollowORM(Base):
    """Database model representing a user follow relationship."""

    __tablename__ = "user_follows"
    __table_args__ = (
        UniqueConstraint("follower_id", "following_id", name="uq_user_follows_follower_following"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    follower_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    following_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(UTC)
    )

    follower_user: Mapped[UserORM] = relationship(
        "UserORM", foreign_keys=[follower_id], back_populates="following"
    )
    following_user: Mapped[UserORM] = relationship(
        "UserORM", foreign_keys=[following_id], back_populates="followers"
    )


class ActivityFeedORM(Base):
    """Database model representing an activity in the user feed."""

    __tablename__ = "activity_feed"
    __table_args__ = (
        CheckConstraint(
            "activity_type IN ('spot_created', 'spot_rated', 'spot_commented', 'spot_favorited', 'spot_checked_in', 'session_created', 'session_rsvp')",
            name="ck_activity_feed_activity_type",
        ),
        CheckConstraint(
            "target_type IN ('spot', 'rating', 'comment', 'favorite', 'check_in', 'session', 'rsvp')",
            name="ck_activity_feed_target_type",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    activity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_id: Mapped[str] = mapped_column(String(36), nullable=False)
    activity_metadata: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(UTC), index=True
    )

    actor: Mapped[UserORM] = relationship("UserORM", back_populates="activities")


class NotificationORM(Base):
    """Database model representing a user notification."""

    __tablename__ = "notifications"
    __table_args__ = (
        CheckConstraint(
            "notification_type IN ('spot_created', 'spot_rated', 'spot_commented', 'spot_favorited', 'spot_checked_in', 'session_created', 'session_rsvp')",
            name="ck_notifications_type",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    actor_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    activity_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("activity_feed.id", ondelete="CASCADE"), nullable=True, index=True
    )
    notification_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    notification_metadata: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        index=True,
    )

    user: Mapped[UserORM] = relationship(
        "UserORM", foreign_keys=[user_id], back_populates="notifications"
    )
    actor: Mapped[UserORM | None] = relationship("UserORM", foreign_keys=[actor_id])
    activity: Mapped[ActivityFeedORM | None] = relationship("ActivityFeedORM")


class SessionORM(Base):
    """Database model representing an organised skate session."""

    __tablename__ = "spot_sessions"
    __table_args__ = (
        CheckConstraint(
            "capacity IS NULL OR capacity >= 1",
            name="ck_spot_sessions_capacity_positive",
        ),
        CheckConstraint(
            "status IN ('scheduled', 'cancelled', 'completed')",
            name="ck_spot_sessions_status_enum",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    spot_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("skate_spots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organizer_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    meet_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    skill_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="scheduled")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
    )

    spot: Mapped[SkateSpotORM] = relationship("SkateSpotORM", back_populates="sessions")
    organizer: Mapped[UserORM] = relationship("UserORM", back_populates="hosted_sessions")
    rsvps: Mapped[list[SessionRSVPORM]] = relationship(
        "SessionRSVPORM",
        back_populates="session",
        cascade="all, delete-orphan",
    )


class SessionRSVPORM(Base):
    """Database model tracking attendance responses for a session."""

    __tablename__ = "session_rsvps"
    __table_args__ = (
        UniqueConstraint("session_id", "user_id", name="uq_session_rsvps_session_user"),
        CheckConstraint(
            "response IN ('going', 'maybe', 'waitlist')",
            name="ck_session_rsvps_response_enum",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("spot_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    response: Mapped[str] = mapped_column(String(20), nullable=False, default="going")
    note: Mapped[str | None] = mapped_column(String(300), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
    )

    session: Mapped[SessionORM] = relationship("SessionORM", back_populates="rsvps")
    user: Mapped[UserORM] = relationship("UserORM", back_populates="session_rsvps")


class SpotCheckInORM(Base):
    """Database model representing a real-time check-in at a skate spot."""

    __tablename__ = "spot_check_ins"
    __table_args__ = (
        CheckConstraint(
            "status IN ('heading', 'arrived')",
            name="ck_spot_check_ins_status",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    spot_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("skate_spots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[str | None] = mapped_column(String(280), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    spot: Mapped[SkateSpotORM] = relationship("SkateSpotORM", back_populates="check_ins")
    user: Mapped[UserORM] = relationship("UserORM", back_populates="check_ins")


class WeatherSnapshotORM(Base):
    """Cached weather payload for a skate spot."""

    __tablename__ = "weather_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    spot_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("skate_spots.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False, default="open-meteo")
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    spot: Mapped[SkateSpotORM] = relationship("SkateSpotORM", back_populates="weather_snapshot")
