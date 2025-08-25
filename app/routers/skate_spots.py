"""REST API endpoints for skate spots."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from app.models.skate_spot import SkateSpot, SkateSpotCreate, SkateSpotUpdate
from app.services.skate_spot_service import skate_spot_service

router = APIRouter(prefix="/skate-spots", tags=["skate-spots"])


@router.post("/", response_model=SkateSpot, status_code=status.HTTP_201_CREATED)
async def create_skate_spot(spot_data: SkateSpotCreate) -> SkateSpot:
    """Create a new skate spot."""
    return skate_spot_service.create_spot(spot_data)


@router.get("/", response_model=list[SkateSpot])
async def list_skate_spots() -> list[SkateSpot]:
    """Get all skate spots."""
    return skate_spot_service.list_spots()


@router.get("/{spot_id}", response_model=SkateSpot)
async def get_skate_spot(spot_id: UUID) -> SkateSpot:
    """Get a specific skate spot by ID."""
    spot = skate_spot_service.get_spot(spot_id)
    if not spot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Skate spot with id {spot_id} not found"
        )
    return spot


@router.put("/{spot_id}", response_model=SkateSpot)
async def update_skate_spot(spot_id: UUID, update_data: SkateSpotUpdate) -> SkateSpot:
    """Update an existing skate spot."""
    updated_spot = skate_spot_service.update_spot(spot_id, update_data)
    if not updated_spot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Skate spot with id {spot_id} not found"
        )
    return updated_spot


@router.delete("/{spot_id}")
async def delete_skate_spot(spot_id: UUID) -> JSONResponse:
    """Delete a skate spot."""
    success = skate_spot_service.delete_spot(spot_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Skate spot with id {spot_id} not found"
        )
    return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)
