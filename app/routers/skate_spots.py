"""REST API endpoints for skate spots."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from pydantic import ValidationError

from app.models.skate_spot import (
    Difficulty,
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

router = APIRouter(prefix="/skate-spots", tags=["skate-spots"])


@router.post("/", response_model=SkateSpot, status_code=status.HTTP_201_CREATED)
async def create_skate_spot(
    request: Request,
    service: Annotated[SkateSpotService, Depends(get_skate_spot_service)],
) -> SkateSpot:
    """Create a new skate spot."""
    content_type = request.headers.get("content-type", "")

    try:
        if "application/json" in content_type:
            # Handle JSON request
            body = await request.json()
            spot_data = SkateSpotCreate(**body)
        else:
            # Handle form data
            form = await request.form()
            location = Location(
                latitude=float(form.get("latitude")),
                longitude=float(form.get("longitude")),
                city=str(form.get("city")),
                country=str(form.get("country")),
                address=form.get("address") or None,
            )
            spot_data = SkateSpotCreate(
                name=str(form.get("name")),
                description=str(form.get("description")),
                spot_type=SpotType(form.get("spot_type")),
                difficulty=Difficulty(form.get("difficulty")),
                location=location,
                is_public=form.get("is_public", "true").lower() in ("true", "on", "1"),
                requires_permission=form.get("requires_permission", "false").lower()
                in ("true", "on", "1"),
            )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.errors()
        ) from None

    return service.create_spot(spot_data)


@router.get("/", response_model=list[SkateSpot])
async def list_skate_spots(
    service: Annotated[SkateSpotService, Depends(get_skate_spot_service)],
) -> list[SkateSpot]:
    """Get all skate spots."""

    return service.list_spots()


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


@router.put("/{spot_id}", response_model=SkateSpot)
async def update_skate_spot(
    spot_id: UUID,
    request: Request,
    service: Annotated[SkateSpotService, Depends(get_skate_spot_service)],
) -> SkateSpot:
    """Update an existing skate spot."""
    content_type = request.headers.get("content-type", "")

    try:
        if "application/json" in content_type:
            # Handle JSON request
            body = await request.json()
            update_data = SkateSpotUpdate(**body)
        else:
            # Handle form data
            form = await request.form()
            location = Location(
                latitude=float(form.get("latitude")),
                longitude=float(form.get("longitude")),
                city=str(form.get("city")),
                country=str(form.get("country")),
                address=form.get("address") or None,
            )
            update_data = SkateSpotUpdate(
                name=str(form.get("name")),
                description=str(form.get("description")),
                spot_type=SpotType(form.get("spot_type")),
                difficulty=Difficulty(form.get("difficulty")),
                location=location,
                is_public=form.get("is_public", "").lower() in ("true", "on", "1"),
                requires_permission=form.get("requires_permission", "").lower()
                in ("true", "on", "1"),
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


@router.delete("/{spot_id}", response_class=HTMLResponse)
async def delete_skate_spot(
    spot_id: UUID,
    service: Annotated[SkateSpotService, Depends(get_skate_spot_service)],
) -> HTMLResponse:
    """Delete a skate spot."""

    success = service.delete_spot(spot_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skate spot with id {spot_id} not found",
        )
    return HTMLResponse(content="", status_code=200)
