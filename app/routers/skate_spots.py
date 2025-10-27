"""REST API endpoints for skate spots."""

from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ValidationError
from starlette.datastructures import UploadFile as StarletteUploadFile

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
from app.services.photo_storage import PhotoStorageError, delete_photos, save_photo_upload
from app.services.skate_spot_service import SkateSpotService, get_skate_spot_service
from app.utils.filters import build_nearby_spot_filters, build_skate_spot_filters

router = APIRouter(prefix="/skate-spots", tags=["skate-spots"])
_TRUE_VALUES = {"true", "on", "1"}


async def _parse_location_from_form(form) -> Location:
    """Parse Location object from form data.

    Args:
        form: Form data containing latitude, longitude, city, country, and optional address

    Returns:
        Location object with parsed coordinates and address information

    Raises:
        ValueError: If coordinates are missing or cannot be parsed as valid numbers
    """
    lat_str = form.get("latitude")
    lng_str = form.get("longitude")

    # Validate coordinates are provided
    if not lat_str or not lng_str:
        raise ValueError("Location coordinates are required.")

    try:
        latitude = float(lat_str)
        longitude = float(lng_str)
    except (ValueError, TypeError):
        raise ValueError("Coordinates must be valid numbers.") from None

    return Location(
        latitude=latitude,
        longitude=longitude,
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


def _extract_uploads(form, field_name: str) -> list[UploadFile]:
    """Return a list of ``UploadFile`` instances for the given form field."""

    uploads = []
    for value in form.getlist(field_name):
        if isinstance(value, UploadFile | StarletteUploadFile):
            uploads.append(value)
    return uploads


async def _store_uploads(
    uploads: list[UploadFile],
) -> tuple[list[dict[str, str | None]], list[str]]:
    """Persist uploads to disk and return payloads plus stored paths for cleanup."""

    stored_payloads: list[dict[str, str | None]] = []
    stored_paths: list[str] = []

    for upload in uploads:
        if not upload.filename:
            await upload.close()
            continue
        try:
            stored = save_photo_upload(upload)
        except PhotoStorageError as exc:
            delete_photos(stored_paths)
            await upload.close()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        else:
            stored_paths.append(stored.path)
            stored_payloads.append(
                {"path": stored.path, "original_filename": stored.original_filename}
            )
        finally:
            await upload.close()

    return stored_payloads, stored_paths


async def _parse_form_for_create(
    request: Request,
    *,
    bool_defaults: dict[str, bool],
) -> tuple[SkateSpotCreate, list[str]]:
    """Parse a multipart form submission when creating a skate spot."""

    form = await request.form()

    try:
        location = await _parse_location_from_form(form)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    uploads = _extract_uploads(form, "photo_files")
    photo_payloads, stored_paths = await _store_uploads(uploads)

    payload = {
        "name": form.get("name"),
        "description": form.get("description"),
        "spot_type": SpotType(form.get("spot_type")),
        "difficulty": Difficulty(form.get("difficulty")),
        "location": location,
        "photos": photo_payloads,
    }
    payload.update(
        {
            field: _coerce_form_bool(form.get(field), default)
            for field, default in bool_defaults.items()
        }
    )

    try:
        return SkateSpotCreate(**payload), stored_paths
    except ValidationError as exc:
        delete_photos(stored_paths)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.errors()
        ) from exc


async def _parse_form_for_update(
    request: Request,
    existing_spot: SkateSpot,
    *,
    bool_defaults: dict[str, bool],
) -> tuple[SkateSpotUpdate, list[str], list[str]]:
    """Parse a multipart form submission when updating a skate spot."""

    form = await request.form()

    try:
        location = await _parse_location_from_form(form)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    uploads = _extract_uploads(form, "photo_files")
    new_photo_payloads, stored_paths = await _store_uploads(uploads)

    delete_photo_ids = {value for value in form.getlist("delete_photo_ids") if value}
    kept_photos = []
    removed_paths = []
    for photo in existing_spot.photos:
        if str(photo.id) in delete_photo_ids:
            removed_paths.append(photo.path)
        else:
            kept_photos.append(
                {
                    "path": photo.path,
                    "original_filename": photo.original_filename,
                }
            )

    payload: dict[str, object] = {
        "name": form.get("name"),
        "description": form.get("description"),
        "spot_type": SpotType(form.get("spot_type")),
        "difficulty": Difficulty(form.get("difficulty")),
        "location": location,
        "photos": kept_photos + new_photo_payloads,
    }
    payload.update(
        {
            field: _coerce_form_bool(form.get(field), default)
            for field, default in bool_defaults.items()
        }
    )

    try:
        return SkateSpotUpdate(**payload), stored_paths, removed_paths
    except ValidationError as exc:
        delete_photos(stored_paths)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.errors()
        ) from exc


async def _parse_request_payload[SchemaT: BaseModel](
    request: Request,
    schema: type[SchemaT],
) -> SchemaT:
    """Normalise request payloads to the desired schema for JSON or form submissions."""

    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        payload = await request.json()
        return schema(**payload)

    raise HTTPException(
        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        detail="Unsupported content type",
    )


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
    content_type = request.headers.get("content-type", "")

    if "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
        spot_data, stored_paths = await _parse_form_for_create(
            request, bool_defaults={"is_public": True, "requires_permission": False}
        )
        try:
            return service.create_spot(spot_data, current_user.id)
        except Exception:
            delete_photos(stored_paths)
            raise

    try:
        spot_data = await _parse_request_payload(request, SkateSpotCreate)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.errors()
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


@router.get("/nearby", response_model=list[SkateSpot])
async def get_nearby_spots(
    service: Annotated[SkateSpotService, Depends(get_skate_spot_service)],
    latitude: float = Query(..., ge=-90, le=90, description="Center point latitude"),
    longitude: float = Query(..., ge=-180, le=180, description="Center point longitude"),
    radius_km: float = Query(5, ge=0.1, le=50, description="Search radius in kilometers"),
    search: str | None = None,
    spot_type: Annotated[list[SpotType] | None, Query()] = None,
    difficulty: Annotated[list[Difficulty] | None, Query()] = None,
    city: str | None = None,
    country: str | None = None,
    is_public: Annotated[bool | None, Query()] = None,
    requires_permission: Annotated[bool | None, Query()] = None,
) -> list[SkateSpot]:
    """Get skate spots within a specified radius of a location.

    Returns spots sorted by distance (closest first) with distance_km field populated.
    """
    try:
        filters = build_nearby_spot_filters(
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            search=search,
            spot_types=spot_type,
            difficulties=difficulty,
            city=city,
            country=country,
            is_public=is_public,
            requires_permission=requires_permission,
        )
        return service.get_nearby_spots(
            latitude=filters.latitude,
            longitude=filters.longitude,
            radius_km=filters.radius_km,
            filters=filters,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


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
    existing_spot = _ensure_spot_can_be_modified(spot_id, service, current_user, action="update")

    content_type = request.headers.get("content-type", "")

    if "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
        update_data, stored_paths, removed_paths = await _parse_form_for_update(
            request,
            existing_spot,
            bool_defaults={"is_public": False, "requires_permission": False},
        )
        try:
            updated_spot = service.update_spot(spot_id, update_data)
        except Exception:
            delete_photos(stored_paths)
            raise
        if not updated_spot:
            delete_photos(stored_paths)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Skate spot with id {spot_id} not found",
            )
        delete_photos(removed_paths)
        return updated_spot

    try:
        update_data = await _parse_request_payload(request, SkateSpotUpdate)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.errors()
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
