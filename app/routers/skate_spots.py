"""REST API endpoints for skate spots."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.models.skate_spot import SkateSpot, SkateSpotCreate, SkateSpotUpdate
from app.services.skate_spot_service import (
    SkateSpotService,
    get_skate_spot_service,
)

router = APIRouter(prefix="/skate-spots", tags=["skate-spots"])


@router.post("/", response_model=SkateSpot, status_code=status.HTTP_201_CREATED)
async def create_skate_spot(
    spot_data: SkateSpotCreate,
    service: Annotated[SkateSpotService, Depends(get_skate_spot_service)],
) -> SkateSpot:
    """Create a new skate spot."""

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
    update_data: SkateSpotUpdate,
    service: Annotated[SkateSpotService, Depends(get_skate_spot_service)],
) -> SkateSpot:
    """Update an existing skate spot."""

    updated_spot = service.update_spot(spot_id, update_data)
    if not updated_spot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skate spot with id {spot_id} not found",
        )
    return updated_spot


@router.delete("/{spot_id}")
async def delete_skate_spot(
    spot_id: UUID,
    service: Annotated[SkateSpotService, Depends(get_skate_spot_service)],
) -> JSONResponse:
    """Delete a skate spot."""

    success = service.delete_spot(spot_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skate spot with id {spot_id} not found",
        )
    return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)
