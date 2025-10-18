"""API endpoints for managing user favourite skate spots."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID  # noqa: TCH003

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_current_user
from app.db.models import UserORM  # noqa: TCH001
from app.models.favorite import FavoriteStatus
from app.models.skate_spot import SkateSpot
from app.services.favorite_service import (
    FavoriteService,
    SpotNotFoundError,
    get_favorite_service,
)

router = APIRouter(prefix="/users/me/favorites", tags=["favorites"])


def _handle_spot_not_found(exc: SpotNotFoundError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/", response_model=list[SkateSpot])
async def list_my_favorites(
    service: Annotated[FavoriteService, Depends(get_favorite_service)],
    current_user: Annotated[UserORM, Depends(get_current_user)],
) -> list[SkateSpot]:
    """Return the authenticated user's favourite skate spots."""

    return service.list_user_favorites(current_user.id)


@router.put(
    "/{spot_id}",
    response_model=FavoriteStatus,
    status_code=status.HTTP_200_OK,
)
async def add_favorite(
    spot_id: UUID,
    service: Annotated[FavoriteService, Depends(get_favorite_service)],
    current_user: Annotated[UserORM, Depends(get_current_user)],
) -> FavoriteStatus:
    """Mark the given skate spot as a favourite for the authenticated user."""

    try:
        return service.add_favorite(spot_id, current_user.id)
    except SpotNotFoundError as exc:
        raise _handle_spot_not_found(exc) from exc


@router.delete(
    "/{spot_id}",
    response_model=FavoriteStatus,
    status_code=status.HTTP_200_OK,
)
async def remove_favorite(
    spot_id: UUID,
    service: Annotated[FavoriteService, Depends(get_favorite_service)],
    current_user: Annotated[UserORM, Depends(get_current_user)],
) -> FavoriteStatus:
    """Remove the given skate spot from the authenticated user's favourites."""

    try:
        return service.remove_favorite(spot_id, current_user.id)
    except SpotNotFoundError as exc:
        raise _handle_spot_not_found(exc) from exc


@router.post(
    "/{spot_id}/toggle",
    response_model=FavoriteStatus,
    status_code=status.HTTP_200_OK,
)
async def toggle_favorite(
    spot_id: UUID,
    service: Annotated[FavoriteService, Depends(get_favorite_service)],
    current_user: Annotated[UserORM, Depends(get_current_user)],
) -> FavoriteStatus:
    """Toggle favourite status for the authenticated user."""

    try:
        return service.toggle_favorite(spot_id, current_user.id)
    except SpotNotFoundError as exc:
        raise _handle_spot_not_found(exc) from exc
