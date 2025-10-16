"""REST API endpoints for ratings."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_current_user
from app.core.rate_limiter import SKATE_SPOT_WRITE_LIMIT, rate_limited
from app.db.models import UserORM
from app.models.rating import Rating, RatingCreate, RatingStats, RatingUpdate
from app.services.rating_service import RatingService, get_rating_service
from app.services.skate_spot_service import SkateSpotService, get_skate_spot_service

router = APIRouter(prefix="/skate-spots/{spot_id}/ratings", tags=["ratings"])


@router.post(
    "/",
    response_model=Rating,
    status_code=status.HTTP_201_CREATED,
    dependencies=[rate_limited(SKATE_SPOT_WRITE_LIMIT)],
)
async def create_rating(
    spot_id: UUID,
    rating_data: RatingCreate,
    service: Annotated[RatingService, Depends(get_rating_service)],
    spot_service: Annotated[SkateSpotService, Depends(get_skate_spot_service)],
    current_user: Annotated[UserORM, Depends(get_current_user)],
) -> Rating:
    """Create a new rating for a skate spot."""
    # Check if spot exists
    spot = spot_service.get_spot(spot_id)
    if not spot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skate spot with id {spot_id} not found",
        )

    # Check if user already rated this spot
    existing_rating = service.get_user_rating_for_spot(spot_id, current_user.id)
    if existing_rating:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already rated this spot",
        )

    return service.create_rating(spot_id, current_user.id, rating_data)


@router.get("/", response_model=list[Rating])
async def list_ratings(
    spot_id: UUID,
    service: Annotated[RatingService, Depends(get_rating_service)],
    spot_service: Annotated[SkateSpotService, Depends(get_skate_spot_service)],
) -> list[Rating]:
    """Get all ratings for a skate spot."""
    # Check if spot exists
    spot = spot_service.get_spot(spot_id)
    if not spot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skate spot with id {spot_id} not found",
        )

    return service.get_spot_ratings(spot_id)


@router.get("/stats", response_model=RatingStats)
async def get_rating_stats(
    spot_id: UUID,
    service: Annotated[RatingService, Depends(get_rating_service)],
    spot_service: Annotated[SkateSpotService, Depends(get_skate_spot_service)],
) -> RatingStats:
    """Get rating statistics for a skate spot."""
    # Check if spot exists
    spot = spot_service.get_spot(spot_id)
    if not spot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skate spot with id {spot_id} not found",
        )

    return service.get_spot_rating_stats(spot_id)


@router.get("/{rating_id}", response_model=Rating)
async def get_rating(
    spot_id: UUID,
    rating_id: UUID,
    service: Annotated[RatingService, Depends(get_rating_service)],
    spot_service: Annotated[SkateSpotService, Depends(get_skate_spot_service)],
) -> Rating:
    """Get a specific rating by ID."""
    # Check if spot exists
    spot = spot_service.get_spot(spot_id)
    if not spot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skate spot with id {spot_id} not found",
        )

    rating = service.get_rating(rating_id)
    if not rating:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rating with id {rating_id} not found",
        )

    # Verify rating belongs to this spot
    if rating.spot_id != spot_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rating with id {rating_id} not found for spot {spot_id}",
        )

    return rating


@router.put(
    "/{rating_id}",
    response_model=Rating,
    dependencies=[rate_limited(SKATE_SPOT_WRITE_LIMIT)],
)
async def update_rating(
    spot_id: UUID,
    rating_id: UUID,
    update_data: RatingUpdate,
    service: Annotated[RatingService, Depends(get_rating_service)],
    spot_service: Annotated[SkateSpotService, Depends(get_skate_spot_service)],
    current_user: Annotated[UserORM, Depends(get_current_user)],
) -> Rating:
    """Update an existing rating."""
    # Check if spot exists
    spot = spot_service.get_spot(spot_id)
    if not spot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skate spot with id {spot_id} not found",
        )

    # Check if rating exists
    rating = service.get_rating(rating_id)
    if not rating:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rating with id {rating_id} not found",
        )

    # Verify rating belongs to this spot
    if rating.spot_id != spot_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rating with id {rating_id} not found for spot {spot_id}",
        )

    # Check ownership (admins can update any rating)
    if not current_user.is_admin and not service.is_owner(rating_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this rating",
        )

    updated_rating = service.update_rating(rating_id, update_data)
    if not updated_rating:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rating with id {rating_id} not found",
        )

    return updated_rating


@router.delete(
    "/{rating_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[rate_limited(SKATE_SPOT_WRITE_LIMIT)],
)
async def delete_rating(
    spot_id: UUID,
    rating_id: UUID,
    service: Annotated[RatingService, Depends(get_rating_service)],
    spot_service: Annotated[SkateSpotService, Depends(get_skate_spot_service)],
    current_user: Annotated[UserORM, Depends(get_current_user)],
) -> None:
    """Delete a rating."""
    # Check if spot exists
    spot = spot_service.get_spot(spot_id)
    if not spot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skate spot with id {spot_id} not found",
        )

    # Check if rating exists
    rating = service.get_rating(rating_id)
    if not rating:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rating with id {rating_id} not found",
        )

    # Verify rating belongs to this spot
    if rating.spot_id != spot_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rating with id {rating_id} not found for spot {spot_id}",
        )

    # Check ownership (admins can delete any rating)
    if not current_user.is_admin and not service.is_owner(rating_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this rating",
        )

    success = service.delete_rating(rating_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rating with id {rating_id} not found",
        )
