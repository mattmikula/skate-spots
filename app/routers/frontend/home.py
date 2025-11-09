"""Home page and navigation routers."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID  # noqa: TCH003

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse

from app.core.dependencies import get_optional_user
from app.db.models import UserORM  # noqa: TCH001
from app.models.skate_spot import Difficulty, SpotType
from app.routers.frontend._shared import (
    _build_service_filters,
    _coerce_enum,
    _coerce_optional_bool,
    _extract_filter_values,
    _has_active_filters,
    _is_htmx,
    _spot_list_context,
    templates,
)
from app.services.favorite_service import (
    FavoriteService,
    get_favorite_service,
)
from app.services.skate_spot_service import SkateSpotService, get_skate_spot_service
from app.utils.filters import build_skate_spot_filters

router = APIRouter(tags=["frontend"])


@router.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    service: Annotated[SkateSpotService, Depends(get_skate_spot_service)],
    favorite_service: Annotated[FavoriteService, Depends(get_favorite_service)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Display home page with all skate spots."""
    filter_values = _extract_filter_values(request)
    filters = _build_service_filters(filter_values)
    spots = service.list_spots(filters)
    favorite_spot_ids = (
        favorite_service.favorite_ids_for_user(current_user.id) if current_user else set()
    )

    context = _spot_list_context(
        request,
        spots,
        current_user,
        filter_values,
        favorite_spot_ids,
    )
    return templates.TemplateResponse("index.html", context)


@router.get("/skate-spots", response_class=HTMLResponse)
async def list_spots_page(
    request: Request,
    service: Annotated[SkateSpotService, Depends(get_skate_spot_service)],
    favorite_service: Annotated[FavoriteService, Depends(get_favorite_service)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Display all skate spots, optionally filtered via HTMX or page loads."""
    filter_values = _extract_filter_values(request)
    filters = _build_service_filters(filter_values)
    spots = service.list_spots(filters)
    favorite_spot_ids = (
        favorite_service.favorite_ids_for_user(current_user.id) if current_user else set()
    )

    template_name = "partials/spot_list.html" if _is_htmx(request) else "index.html"
    context = _spot_list_context(
        request,
        spots,
        current_user,
        filter_values,
        favorite_spot_ids,
    )
    return templates.TemplateResponse(template_name, context)


@router.get("/nearby", response_class=HTMLResponse)
async def nearby_spots_page(
    request: Request,
    service: Annotated[SkateSpotService, Depends(get_skate_spot_service)],
    favorite_service: Annotated[FavoriteService, Depends(get_favorite_service)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Display nearby skate spots based on latitude/longitude parameters."""
    # Extract location and filter parameters
    latitude_str = request.query_params.get("latitude", "").strip()
    longitude_str = request.query_params.get("longitude", "").strip()
    radius_km_str = request.query_params.get("radius_km", "5").strip()

    # If no location provided, show the location input form
    if not latitude_str or not longitude_str:
        context = {
            "request": request,
            "current_user": current_user,
            "spot_types": list(SpotType),
            "difficulties": list(Difficulty),
        }
        return templates.TemplateResponse("nearby.html", context)

    # Parse coordinates and radius
    try:
        latitude = float(latitude_str)
        longitude = float(longitude_str)
        radius_km = float(radius_km_str)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid coordinates or radius",
        ) from exc

    # Extract additional filters
    filter_values = _extract_filter_values(request)
    spot_type = _coerce_enum(filter_values["spot_type"], SpotType)
    difficulty = _coerce_enum(filter_values["difficulty"], Difficulty)

    filters = build_skate_spot_filters(
        search=filter_values["search"] or None,
        spot_types=[spot_type] if spot_type else None,
        difficulties=[difficulty] if difficulty else None,
        city=filter_values["city"] or None,
        country=filter_values["country"] or None,
        is_public=_coerce_optional_bool(filter_values["is_public"]),
        requires_permission=_coerce_optional_bool(filter_values["requires_permission"]),
    )

    # Get nearby spots
    try:
        spots = service.get_nearby_spots(latitude, longitude, radius_km, filters)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    favorite_spot_ids = (
        favorite_service.favorite_ids_for_user(current_user.id) if current_user else set()
    )

    template_name = "partials/nearby_spot_list.html" if _is_htmx(request) else "nearby.html"
    context = {
        "request": request,
        "spots": spots,
        "current_user": current_user,
        "spot_types": list(SpotType),
        "difficulties": list(Difficulty),
        "filter_values": filter_values,
        "has_active_filters": _has_active_filters(filter_values),
        "favorite_spot_ids": favorite_spot_ids or set(),
        "latitude": latitude,
        "longitude": longitude,
        "radius_km": radius_km,
    }
    return templates.TemplateResponse(template_name, context)


@router.get("/map", response_class=HTMLResponse)
async def map_view(
    request: Request,
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Display interactive map of all skate spots."""
    return templates.TemplateResponse(
        "map.html",
        {"request": request, "current_user": current_user},
    )
