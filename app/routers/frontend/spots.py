"""Skate spot page routers."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID  # noqa: TCH003

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from app.core.dependencies import get_optional_user
from app.db.models import UserORM  # noqa: TCH001
from app.routers.frontend._shared import templates
from app.services.favorite_service import (
    FavoriteService,
    get_favorite_service,
)
from app.services.skate_spot_service import SkateSpotService, get_skate_spot_service
from app.services.weather_service import (
    WeatherService,
    WeatherSpotNotFoundError,
    WeatherUnavailableError,
    get_weather_service,
)

router = APIRouter(tags=["frontend"])


@router.get("/skate-spots/new", response_class=HTMLResponse)
async def new_spot_page(
    request: Request,
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Display form to create a new skate spot."""
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(
        "spot_form.html",
        {"request": request, "spot": None, "current_user": current_user},
    )


@router.get("/skate-spots/{spot_id}", response_class=HTMLResponse)
async def spot_detail_page(
    request: Request,
    spot_id: UUID,
    service: Annotated[SkateSpotService, Depends(get_skate_spot_service)],
    favorite_service: Annotated[FavoriteService, Depends(get_favorite_service)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Display detailed view of a single skate spot."""
    spot = service.get_spot(spot_id)
    if not spot:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "title": "Spot not found",
                "message": "The requested skate spot could not be found.",
                "current_user": current_user,
            },
            status_code=status.HTTP_404_NOT_FOUND,
        )

    favorite_spot_ids = (
        favorite_service.favorite_ids_for_user(current_user.id) if current_user else set()
    )

    is_owner = False
    if current_user:
        is_owner = service.is_owner(spot_id, current_user.id)

    return templates.TemplateResponse(
        "spot_detail.html",
        {
            "request": request,
            "spot": spot,
            "current_user": current_user,
            "favorite_spot_ids": favorite_spot_ids,
            "is_owner": is_owner,
        },
    )


@router.get("/skate-spots/{spot_id}/weather", response_class=HTMLResponse)
async def spot_weather_section(
    request: Request,
    spot_id: UUID,
    weather_service: Annotated[WeatherService, Depends(get_weather_service)],
    force_refresh: bool = Query(
        default=False,
        description="Force refresh from provider rather than using cached data",
    ),
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Render the weather card partial for a spot."""

    try:
        snapshot = weather_service.get_weather_for_spot(spot_id, force_refresh=force_refresh)
        error = None
        status_code = status.HTTP_200_OK
    except WeatherSpotNotFoundError as exc:
        snapshot = None
        error = str(exc)
        status_code = status.HTTP_404_NOT_FOUND
    except WeatherUnavailableError:
        snapshot = None
        error = "Weather information is temporarily unavailable."
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return templates.TemplateResponse(
        "partials/spot_weather.html",
        {
            "request": request,
            "spot_id": spot_id,
            "weather": snapshot,
            "current_user": current_user,
            "error": error,
        },
        status_code=status_code,
    )


@router.get("/skate-spots/{spot_id}/edit", response_class=HTMLResponse)
async def edit_spot_page(
    request: Request,
    spot_id: UUID,
    service: Annotated[SkateSpotService, Depends(get_skate_spot_service)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Display form to edit an existing skate spot."""
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    spot = service.get_spot(spot_id)
    if not spot:
        return RedirectResponse(url="/", status_code=303)

    # Check if user owns the spot or is admin
    if not current_user.is_admin and not service.is_owner(spot_id, current_user.id):
        return RedirectResponse(url="/", status_code=303)

    return templates.TemplateResponse(
        "spot_form.html",
        {"request": request, "spot": spot, "current_user": current_user},
    )
