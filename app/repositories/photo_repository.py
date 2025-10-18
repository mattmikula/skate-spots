"""Repository layer for skate spot photos."""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db.models import SpotPhotoORM
from app.models.photo import SpotPhoto, SpotPhotoCreate

SessionFactory = Callable[[], Session]


def _orm_to_pydantic(orm_photo: SpotPhotoORM) -> SpotPhoto:
    """Convert an ORM instance into a Pydantic model."""
    return SpotPhoto(
        id=UUID(orm_photo.id),
        spot_id=UUID(orm_photo.spot_id),
        user_id=orm_photo.user_id,
        filename=orm_photo.filename,
        file_path=orm_photo.file_path,
        caption=orm_photo.caption,
        is_primary=orm_photo.is_primary,
        created_at=orm_photo.created_at,
    )


class PhotoRepository:
    """Repository handling database persistence for spot photos."""

    def __init__(self, session_factory: SessionFactory | None = None) -> None:
        self._session_factory = session_factory or SessionLocal

    def create(
        self,
        photo_data: SpotPhotoCreate,
        spot_id: UUID,
        user_id: str,
        filename: str,
        file_path: str,
    ) -> SpotPhoto:
        """Create a new spot photo record.

        Args:
            photo_data: The photo creation data
            spot_id: ID of the associated skate spot
            user_id: ID of the user uploading the photo
            filename: The stored filename
            file_path: The file path relative to uploads root

        Returns:
            The created SpotPhoto
        """
        orm_photo = SpotPhotoORM(
            spot_id=str(spot_id),
            user_id=user_id,
            filename=filename,
            file_path=file_path,
            caption=photo_data.caption,
            is_primary=photo_data.is_primary,
        )

        with self._session_factory() as session:
            session.add(orm_photo)
            session.commit()
            session.refresh(orm_photo)
            return _orm_to_pydantic(orm_photo)

    def get_by_id(self, photo_id: UUID) -> SpotPhoto | None:
        """Get a photo by ID.

        Args:
            photo_id: The photo ID

        Returns:
            The SpotPhoto or None if not found
        """
        with self._session_factory() as session:
            orm_photo = session.get(SpotPhotoORM, str(photo_id))
            if orm_photo is None:
                return None
            return _orm_to_pydantic(orm_photo)

    def get_by_spot(self, spot_id: UUID) -> list[SpotPhoto]:
        """Get all photos for a specific spot.

        Args:
            spot_id: The spot ID

        Returns:
            List of photos for the spot, ordered by creation date (newest first)
        """
        with self._session_factory() as session:
            stmt = (
                select(SpotPhotoORM)
                .where(SpotPhotoORM.spot_id == str(spot_id))
                .order_by(SpotPhotoORM.created_at.desc())
            )
            orm_photos = session.scalars(stmt).all()
            return [_orm_to_pydantic(photo) for photo in orm_photos]

    def delete(self, photo_id: UUID) -> bool:
        """Delete a photo by ID.

        Args:
            photo_id: The photo ID

        Returns:
            True if deleted, False if not found
        """
        with self._session_factory() as session:
            orm_photo = session.get(SpotPhotoORM, str(photo_id))
            if orm_photo is None:
                return False
            session.delete(orm_photo)
            session.commit()
            return True

    def set_primary(self, photo_id: UUID, spot_id: UUID) -> bool:
        """Set a photo as the primary photo for a spot.

        This will unset any previously primary photo for the same spot.

        Args:
            photo_id: The photo ID to make primary
            spot_id: The spot ID

        Returns:
            True if successful, False if photo not found
        """
        with self._session_factory() as session:
            # Unset previous primary photo
            stmt = select(SpotPhotoORM).where(
                SpotPhotoORM.spot_id == str(spot_id),
                SpotPhotoORM.is_primary,
            )
            previous_primary = session.scalar(stmt)
            if previous_primary:
                previous_primary.is_primary = False

            # Set new primary photo
            orm_photo = session.get(SpotPhotoORM, str(photo_id))
            if orm_photo is None:
                return False

            orm_photo.is_primary = True
            session.add(orm_photo)
            session.commit()
            return True

    def get_primary_by_spot(self, spot_id: UUID) -> SpotPhoto | None:
        """Get the primary photo for a spot.

        Args:
            spot_id: The spot ID

        Returns:
            The primary SpotPhoto or None if no primary photo exists
        """
        with self._session_factory() as session:
            stmt = select(SpotPhotoORM).where(
                SpotPhotoORM.spot_id == str(spot_id),
                SpotPhotoORM.is_primary,
            )
            orm_photo = session.scalar(stmt)
            if orm_photo is None:
                return None
            return _orm_to_pydantic(orm_photo)

    def is_owner(self, photo_id: UUID, user_id: str) -> bool:
        """Check if a user owns a photo.

        Args:
            photo_id: The photo ID
            user_id: The user ID

        Returns:
            True if the user is the photo owner, False otherwise
        """
        with self._session_factory() as session:
            orm_photo = session.get(SpotPhotoORM, str(photo_id))
            if orm_photo is None:
                return False
            return orm_photo.user_id == user_id
