"""REST API endpoints for skate spots."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse
from pydantic import ValidationError

from app.core.dependencies import get_current_user
from app.core.rate_limiter import SKATE_SPOT_WRITE_LIMIT, rate_limited
from app.db.models import UserORM
from app.models.skate_spot import (
    Difficulty,
    GeoJSONFeature,
    GeoJSONFeatureCollection,
    GeoJSONFeatureProperties,
    GeoJSONPoint,
    Location,
    SkateSpot,
    SkateSpotCreate,
    SkateSpotFilters,
    SkateSpotUpdate,
    SpotType,
)
from app.services.skate_spot_service import (
    SkateSpotService,
    get_skate_spot_service,
)

router = APIRouter(prefix="/skate-spots", tags=["skate-spots"])


async def _parse_location_from_form(form) -> Location:
    """Parse Location object from form data."""
    return Location(
        latitude=float(form.get("latitude")),
        longitude=float(form.get("longitude")),
        city=str(form.get("city")),
        country=str(form.get("country")),
        address=form.get("address") or None,
    )


async def _parse_create_from_form(form) -> SkateSpotCreate:
    """Parse SkateSpotCreate object from form data."""
    location = await _parse_location_from_form(form)
    return SkateSpotCreate(
        name=str(form.get("name")),
        description=str(form.get("description")),
        spot_type=SpotType(form.get("spot_type")),
        difficulty=Difficulty(form.get("difficulty")),
        location=location,
        is_public=form.get("is_public", "true").lower() in ("true", "on", "1"),
        requires_permission=form.get("requires_permission", "false").lower() in ("true", "on", "1"),
    )


async def _parse_update_from_form(form) -> SkateSpotUpdate:
    """Parse SkateSpotUpdate object from form data."""
    location = await _parse_location_from_form(form)
    return SkateSpotUpdate(
        name=str(form.get("name")),
        description=str(form.get("description")),
        spot_type=SpotType(form.get("spot_type")),
        difficulty=Difficulty(form.get("difficulty")),
        location=location,
        is_public=form.get("is_public", "").lower() in ("true", "on", "1"),
        requires_permission=form.get("requires_permission", "").lower() in ("true", "on", "1"),
    )


@router.post(
    "/",
    response_model=SkateSpot,
    status_code=status.HTTP_201_CREATED,
    dependencies=[rate_limited(SKATE_SPOT_WRITE_LIMIT)],
)
async def create_skate_spot(
    request: Request,
    service: Annotated[SkateSpotService, Depends(get_skate_spot_service)],
    current_user: Annotated[UserORM, Depends(get_current_user)],
) -> SkateSpot:
    """Create a new skate spot."""
    try:
        content_type = request.headers.get("content-type", "")
        spot_data = (
            SkateSpotCreate(**(await request.json()))
            if "application/json" in content_type
            else await _parse_create_from_form(await request.form())
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.errors()
        ) from None

    return service.create_spot(spot_data, current_user.id)


def _build_filters(
    search: str | None,
    spot_types: list[SpotType] | None,
    difficulties: list[Difficulty] | None,
    city: str | None,
    country: str | None,
    is_public: bool | None,
    requires_permission: bool | None,
) -> SkateSpotFilters | None:
    filters = SkateSpotFilters(
        search=search,
        spot_types=spot_types or None,
        difficulties=difficulties or None,
        city=city,
        country=country,
        is_public=is_public,
        requires_permission=requires_permission,
    )
    return filters if filters.has_filters() else None


@router.get("/", response_model=list[SkateSpot])
async def list_skate_spots(
    service: Annotated[SkateSpotService, Depends(get_skate_spot_service)],
    search: str | None = None,
    spot_type: Annotated[list[SpotType] | None, Query()] = None,
    difficulty: Annotated[list[Difficulty] | None, Query()] = None,
    city: str | None = None,
    country: str | None = None,
    is_public: Annotated[bool | None, Query()] = None,
    requires_permission: Annotated[bool | None, Query()] = None,
) -> list[SkateSpot]:
    """Get skate spots, optionally filtered by query parameters."""

    filters = _build_filters(
        search=search,
        spot_types=spot_type,
        difficulties=difficulty,
        city=city,
        country=country,
        is_public=is_public,
        requires_permission=requires_permission,
    )

    return service.list_spots(filters)


@router.get("/geojson", response_model=GeoJSONFeatureCollection)
async def get_spots_geojson(
    service: Annotated[SkateSpotService, Depends(get_skate_spot_service)],
    search: str | None = None,
    spot_type: Annotated[list[SpotType] | None, Query()] = None,
    difficulty: Annotated[list[Difficulty] | None, Query()] = None,
    city: str | None = None,
    country: str | None = None,
    is_public: Annotated[bool | None, Query()] = None,
    requires_permission: Annotated[bool | None, Query()] = None,
) -> GeoJSONFeatureCollection:
    """Get skate spots in GeoJSON format, honoring optional filters."""
    spots = service.list_spots(
        _build_filters(
            search=search,
            spot_types=spot_type,
            difficulties=difficulty,
            city=city,
            country=country,
            is_public=is_public,
            requires_permission=requires_permission,
        )
    )

    features = [
        GeoJSONFeature(
            geometry=GeoJSONPoint(coordinates=(spot.location.longitude, spot.location.latitude)),
            properties=GeoJSONFeatureProperties(
                id=str(spot.id),
                name=spot.name,
                description=spot.description,
                spot_type=spot.spot_type.value,
                difficulty=spot.difficulty.value,
                city=spot.location.city,
                country=spot.location.country,
                address=spot.location.address,
                is_public=spot.is_public,
                requires_permission=spot.requires_permission,
            ),
        )
        for spot in spots
    ]

    return GeoJSONFeatureCollection(features=features)


@router.get("/{spot_id}", response_model=SkateSpot)
async def get_skate_spot(
    spot_id: UUID,
    service: Annotated[SkateSpotService, Depends(get_skate_spot_service)],
) -> SkateSpot:
    """Get a specific skate spot by ID."""

    spot = service.get_spot(spot_id)
    if not spot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skate spot with id {spot_id} not found",
        )
    return spot


@router.put(
    "/{spot_id}",
    response_model=SkateSpot,
    dependencies=[rate_limited(SKATE_SPOT_WRITE_LIMIT)],
)
async def update_skate_spot(
    spot_id: UUID,
    request: Request,
    service: Annotated[SkateSpotService, Depends(get_skate_spot_service)],
    current_user: Annotated[UserORM, Depends(get_current_user)],
) -> SkateSpot:
    """Update an existing skate spot."""
    # Check if spot exists
    spot = service.get_spot(spot_id)
    if not spot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skate spot with id {spot_id} not found",
        )

    # Check ownership (admins can update any spot)
    if not current_user.is_admin and not service.is_owner(spot_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this spot",
        )

    try:
        content_type = request.headers.get("content-type", "")
        update_data = (
            SkateSpotUpdate(**(await request.json()))
            if "application/json" in content_type
            else await _parse_update_from_form(await request.form())
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.errors()
        ) from None

    updated_spot = service.update_spot(spot_id, update_data)
    if not updated_spot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skate spot with id {spot_id} not found",
        )
    return updated_spot


@router.delete(
    "/{spot_id}",
    response_class=HTMLResponse,
    dependencies=[rate_limited(SKATE_SPOT_WRITE_LIMIT)],
)
async def delete_skate_spot(
    spot_id: UUID,
    service: Annotated[SkateSpotService, Depends(get_skate_spot_service)],
    current_user: Annotated[UserORM, Depends(get_current_user)],
) -> HTMLResponse:
    """Delete a skate spot."""
    # Check if spot exists
    spot = service.get_spot(spot_id)
    if not spot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skate spot with id {spot_id} not found",
        )

    # Check ownership (admins can delete any spot)
    if not current_user.is_admin and not service.is_owner(spot_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this spot",
        )

    success = service.delete_spot(spot_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skate spot with id {spot_id} not found",
        )
    return HTMLResponse(content="", status_code=200)
