"""REST API endpoints for spot photos."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.core.dependencies import get_current_user
from app.core.rate_limiter import SKATE_SPOT_WRITE_LIMIT, rate_limited
from app.db.models import UserORM
from app.models.photo import PhotoUploadResponse, SpotPhoto
from app.repositories.photo_repository import PhotoRepository
from app.services.photo_service import PhotoService, PhotoStorageError

router = APIRouter(prefix="/api/v1/skate-spots", tags=["photos"])


def get_photo_service() -> PhotoService:
    """Dependency to provide PhotoService."""
    return PhotoService()


def get_photo_repository() -> PhotoRepository:
    """Dependency to provide PhotoRepository."""
    return PhotoRepository()


@router.post(
    "/{spot_id}/photos",
    response_model=PhotoUploadResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[rate_limited(SKATE_SPOT_WRITE_LIMIT)],
)
async def upload_photo(
    spot_id: UUID,
    file: Annotated[UploadFile, File(...)],
    caption: Annotated[str | None, Form()] = None,
    is_primary: Annotated[bool, Form()] = False,
    service: Annotated[PhotoService, Depends(get_photo_service)] = None,
    repository: Annotated[PhotoRepository, Depends(get_photo_repository)] = None,
    current_user: Annotated[UserORM, Depends(get_current_user)] = None,
) -> PhotoUploadResponse:
    """Upload a photo for a skate spot.

    Only authenticated users can upload photos.
    """
    if not service:
        service = get_photo_service()
    if not repository:
        repository = get_photo_repository()

    try:
        # Save the file
        stored_filename, file_path = await service.save_photo(file)

        # Save metadata to database
        photo_data_create = None

        # Create photo metadata
        from app.models.photo import SpotPhotoCreate

        photo_data_create = SpotPhotoCreate(
            caption=caption,
            is_primary=is_primary,
        )

        photo = repository.create(
            photo_data=photo_data_create,
            spot_id=spot_id,
            user_id=current_user.id,
            filename=stored_filename,
            file_path=file_path,
        )

        return PhotoUploadResponse(
            photo=photo,
            message="Photo uploaded successfully",
        )

    except PhotoStorageError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload photo",
        ) from e


@router.get("/{spot_id}/photos", response_model=list[SpotPhoto])
async def list_spot_photos(
    spot_id: UUID,
    repository: Annotated[PhotoRepository, Depends(get_photo_repository)] = None,
) -> list[SpotPhoto]:
    """Get all photos for a specific spot, ordered by newest first."""
    if not repository:
        repository = get_photo_repository()

    return repository.get_by_spot(spot_id)


@router.delete(
    "/{spot_id}/photos/{photo_id}",
    dependencies=[rate_limited(SKATE_SPOT_WRITE_LIMIT)],
)
async def delete_photo(
    photo_id: UUID,
    service: Annotated[PhotoService, Depends(get_photo_service)] = None,
    repository: Annotated[PhotoRepository, Depends(get_photo_repository)] = None,
    current_user: Annotated[UserORM, Depends(get_current_user)] = None,
) -> dict[str, str]:
    """Delete a photo.

    Only the photo owner or admins can delete photos.
    """
    if not service:
        service = get_photo_service()
    if not repository:
        repository = get_photo_repository()

    photo = repository.get_by_id(photo_id)
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found",
        )

    # Check authorization
    if not current_user.is_admin and photo.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this photo",
        )

    # Delete the file from storage
    service.delete_photo(photo.file_path)

    # Delete the database record
    repository.delete(photo_id)

    return {"message": "Photo deleted successfully"}


@router.put(
    "/{spot_id}/photos/{photo_id}/primary",
    response_model=SpotPhoto,
    dependencies=[rate_limited(SKATE_SPOT_WRITE_LIMIT)],
)
async def set_primary_photo(
    spot_id: UUID,
    photo_id: UUID,
    repository: Annotated[PhotoRepository, Depends(get_photo_repository)] = None,
    current_user: Annotated[UserORM, Depends(get_current_user)] = None,
) -> SpotPhoto:
    """Set a photo as the primary/featured photo for a spot.

    Only the photo owner or admins can set photos as primary.
    """
    if not repository:
        repository = get_photo_repository()

    photo = repository.get_by_id(photo_id)
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found",
        )

    # Check authorization
    if not current_user.is_admin and photo.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this photo",
        )

    # Set as primary
    success = repository.set_primary(photo_id, spot_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set primary photo",
        )

    # Return updated photo
    updated_photo = repository.get_by_id(photo_id)
    if not updated_photo:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve updated photo",
        )

    return updated_photo
