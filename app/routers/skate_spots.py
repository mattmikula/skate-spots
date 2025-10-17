"""REST API endpoints for skate spots."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ValidationError

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
    SkateSpotUpdate,
    SpotType,
)
from app.services.skate_spot_service import (
    SkateSpotService,
    get_skate_spot_service,
)
from spots.filters import build_skate_spot_filters

router = APIRouter(prefix="/skate-spots", tags=["skate-spots"])
_TRUE_VALUES = {"true", "on", "1"}


async def _parse_location_from_form(form) -> Location:
    """Parse Location object from form data."""
    return Location(
        latitude=float(form.get("latitude")),
        longitude=float(form.get("longitude")),
        city=str(form.get("city")),
        country=str(form.get("country")),
        address=form.get("address") or None,
    )


def _coerce_form_bool(value: str | None, default: bool) -> bool:
    """Coerce form checkbox values to booleans with sensible defaults."""

    if value is None:
        return default
    normalised = str(value).strip().lower()
    if not normalised:
        return default
    return normalised in _TRUE_VALUES


async def _parse_request_payload[SchemaT: BaseModel](
    request: Request,
    schema: type[SchemaT],
    *,
    bool_defaults: dict[str, bool],
) -> SchemaT:
    """Normalise request payloads to the desired schema for JSON or form submissions."""

    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        payload = await request.json()
        return schema(**payload)

    form = await request.form()
    location = await _parse_location_from_form(form)
    payload = {
        "name": form.get("name"),
        "description": form.get("description"),
        "spot_type": SpotType(form.get("spot_type")),
        "difficulty": Difficulty(form.get("difficulty")),
        "location": location,
    }
    payload.update(
        {
            field: _coerce_form_bool(form.get(field), default)
            for field, default in bool_defaults.items()
        }
    )
    return schema(**payload)


def _ensure_spot_can_be_modified(
    spot_id: UUID,
    service: SkateSpotService,
    current_user: UserORM,
    *,
    action: str = "modify",
) -> SkateSpot:
    """Return the target spot or raise when it cannot be edited by the user."""

    spot = service.get_spot(spot_id)
    if not spot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skate spot with id {spot_id} not found",
        )

    if not current_user.is_admin and not service.is_owner(spot_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Not authorized to {action} this spot",
        )
    return spot


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
        spot_data = await _parse_request_payload(
            request,
            SkateSpotCreate,
            bool_defaults={"is_public": True, "requires_permission": False},
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.errors()
        ) from None

    return service.create_spot(spot_data, current_user.id)


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

    filters = build_skate_spot_filters(
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
        build_skate_spot_filters(
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
    _ensure_spot_can_be_modified(spot_id, service, current_user, action="update")

    try:
        update_data = await _parse_request_payload(
            request,
            SkateSpotUpdate,
            bool_defaults={"is_public": False, "requires_permission": False},
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
    _ensure_spot_can_be_modified(spot_id, service, current_user, action="delete")
    success = service.delete_spot(spot_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skate spot with id {spot_id} not found",
        )
    return HTMLResponse(content="", status_code=200)
