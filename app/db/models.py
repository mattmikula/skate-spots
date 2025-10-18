"""SQLAlchemy ORM models for the application."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
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
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
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
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
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
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    spot: Mapped[SkateSpotORM] = relationship("SkateSpotORM", back_populates="ratings")
    user: Mapped[UserORM] = relationship("UserORM", back_populates="ratings")


class FavoriteSpotORM(Base):
    """Association table linking users to their favourite skate spots."""

    __tablename__ = "favorite_spots"
    __table_args__ = (
        UniqueConstraint("user_id", "spot_id", name="uq_favorite_user_spot"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    spot_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("skate_spots.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    user: Mapped[UserORM] = relationship("UserORM", back_populates="favorite_spots")
    spot: Mapped[SkateSpotORM] = relationship("SkateSpotORM", back_populates="favorited_by")
