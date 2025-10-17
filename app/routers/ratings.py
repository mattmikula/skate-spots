"""API endpoints for managing skate spot ratings."""

from __future__ import annotations

import uuid  # noqa: TC003
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_current_user, get_optional_user
from app.core.rate_limiter import SKATE_SPOT_WRITE_LIMIT, rate_limited
from app.db.models import UserORM  # noqa: TC001
from app.models.rating import Rating, RatingCreate, RatingSummaryResponse
from app.services.rating_service import (
    RatingNotFoundError,
    RatingService,
    SpotNotFoundError,
    get_rating_service,
)

router = APIRouter(prefix="/skate-spots/{spot_id}/ratings", tags=["ratings"])


def _handle_spot_not_found(exc: SpotNotFoundError) -> HTTPException:
    """Convert a SpotNotFoundError into an HTTPException."""

    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/summary", response_model=RatingSummaryResponse)
async def get_ratings_summary(
    spot_id: uuid.UUID,
    service: Annotated[RatingService, Depends(get_rating_service)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)],
) -> RatingSummaryResponse:
    """Return the rating summary for a skate spot, including the current user's rating if present."""

    try:
        user_id = current_user.id if current_user else None
        return service.get_summary(spot_id, user_id)
    except SpotNotFoundError as exc:
        raise _handle_spot_not_found(exc) from exc


@router.get("/me", response_model=Rating)
async def get_my_rating(
    spot_id: uuid.UUID,
    service: Annotated[RatingService, Depends(get_rating_service)],
    current_user: Annotated[UserORM, Depends(get_current_user)],
) -> Rating:
    """Return the authenticated user's rating for the specified skate spot."""

    try:
        return service.get_user_rating(spot_id, current_user.id)
    except SpotNotFoundError as exc:
        raise _handle_spot_not_found(exc) from exc
    except RatingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put(
    "/me",
    response_model=RatingSummaryResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[rate_limited(SKATE_SPOT_WRITE_LIMIT)],
)
async def upsert_my_rating(
    spot_id: uuid.UUID,
    rating: RatingCreate,
    service: Annotated[RatingService, Depends(get_rating_service)],
    current_user: Annotated[UserORM, Depends(get_current_user)],
) -> RatingSummaryResponse:
    """Create or update the authenticated user's rating for a skate spot."""

    try:
        return service.set_rating(spot_id, current_user.id, rating)
    except SpotNotFoundError as exc:
        raise _handle_spot_not_found(exc) from exc


@router.delete(
    "/me",
    response_model=RatingSummaryResponse,
    dependencies=[rate_limited(SKATE_SPOT_WRITE_LIMIT)],
)
async def delete_my_rating(
    spot_id: uuid.UUID,
    service: Annotated[RatingService, Depends(get_rating_service)],
    current_user: Annotated[UserORM, Depends(get_current_user)],
) -> RatingSummaryResponse:
    """Remove the authenticated user's rating for the specified skate spot."""

    try:
        return service.delete_rating(spot_id, current_user.id)
    except SpotNotFoundError as exc:
        raise _handle_spot_not_found(exc) from exc
    except RatingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
