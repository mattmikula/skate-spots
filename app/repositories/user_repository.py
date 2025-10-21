"""Repository for user database operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.db.models import UserORM

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

    from app.models.user import UserCreate, UserProfileUpdate


class UserRepository:
    """Repository for managing user database operations."""

    def __init__(self, db: Session) -> None:
        """Initialize the repository with a database session."""
        self.db = db

    def get_by_id(self, user_id: UUID | str) -> UserORM | None:
        """Get a user by ID."""
        return self.db.query(UserORM).filter(UserORM.id == str(user_id)).first()

    def get_by_email(self, email: str) -> UserORM | None:
        """Get a user by email."""
        return self.db.query(UserORM).filter(UserORM.email == email).first()

    def get_by_username(self, username: str) -> UserORM | None:
        """Get a user by username."""
        return self.db.query(UserORM).filter(UserORM.username == username).first()

    def create(self, user_data: UserCreate, hashed_password: str) -> UserORM:
        """Create a new user."""
        db_user = UserORM(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def list_all(self) -> list[UserORM]:
        """Get all users."""
        return list(self.db.query(UserORM).all())

    def update_profile(self, user: UserORM, profile_data: UserProfileUpdate) -> UserORM:
        """Persist editable profile fields for the given user."""

        updates = profile_data.model_dump(exclude_unset=True)
        for field, value in updates.items():
            setattr(user, field, value)

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
