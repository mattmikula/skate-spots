"""Favorite toggle router."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID  # noqa: TCH003

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import HTMLResponse

from app.core.dependencies import get_optional_user
from app.db.models import UserORM  # noqa: TCH001
from app.routers.frontend._shared import templates
from app.services.favorite_service import (
    FavoriteService,
    get_favorite_service,
)
from app.services.favorite_service import (
    SpotNotFoundError as FavoriteSpotNotFoundError,
)



router = APIRouter(tags=["frontend"])


@router.post(
    "/skate-spots/{spot_id}/favorite",
    response_class=HTMLResponse,
)
async def toggle_favorite_button(
    request: Request,
    spot_id: UUID,
    favorite_service: Annotated[FavoriteService, Depends(get_favorite_service)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)],
) -> HTMLResponse:
    """Toggle the favorite state for the current user and return the button snippet."""
    if current_user is None:
        return templates.TemplateResponse(
            "partials/favorite_button.html",
            {
                "request": request,
                "spot_id": spot_id,
                "is_favorite": False,
                "current_user": None,
                "message": "Log in to save this spot.",
            },
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    try:
        favorite_status = favorite_service.toggle_favorite(spot_id, current_user.id)
    except FavoriteSpotNotFoundError:
        return templates.TemplateResponse(
            "partials/favorite_button.html",
            {
                "request": request,
                "spot_id": spot_id,
                "is_favorite": False,
                "current_user": current_user,
                "message": "This skate spot is no longer available.",
            },
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return templates.TemplateResponse(
        "partials/favorite_button.html",
        {
            "request": request,
            "spot_id": spot_id,
            "is_favorite": favorite_status.is_favorite,
            "current_user": current_user,
            "message": "Added to your favorites."
            if favorite_status.is_favorite
            else "Removed from favorites.",
        },
    )
