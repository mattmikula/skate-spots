"""REST API endpoints for geocoding."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.services.geocoding_service import GeocodingService, get_geocoding_service

router = APIRouter(prefix="/geocoding", tags=["geocoding"])


class GeocodingResponse(BaseModel):
    """Response model for geocoding results."""

    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    address: str | None = Field(None, description="Full address")
    city: str | None = Field(None, description="City name")
    country: str | None = Field(None, description="Country name")


@router.get("/reverse", response_model=GeocodingResponse)
async def reverse_geocode(
    latitude: Annotated[float, Query(ge=-90, le=90)],
    longitude: Annotated[float, Query(ge=-180, le=180)],
    service: Annotated[GeocodingService, Depends(get_geocoding_service)],
) -> GeocodingResponse:
    """
    Convert coordinates to address information.

    This endpoint performs reverse geocoding to convert latitude/longitude
    coordinates into human-readable address information.
    """
    result = service.reverse_geocode(latitude, longitude)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not find address for the given coordinates",
        )

    return GeocodingResponse(
        latitude=result.latitude,
        longitude=result.longitude,
        address=result.address,
        city=result.city,
        country=result.country,
    )


@router.get("/search", response_model=list[GeocodingResponse])
async def search_address(
    service: Annotated[GeocodingService, Depends(get_geocoding_service)],
    q: Annotated[str, Query(min_length=1, description="Search query")],
    limit: Annotated[int, Query(ge=1, le=10)] = 5,
) -> list[GeocodingResponse]:
    """
    Search for locations matching a query string.

    This endpoint performs forward geocoding to convert an address or place name
    into coordinates and detailed location information.
    """
    results = service.search_address(q, limit=limit)

    return [
        GeocodingResponse(
            latitude=result.latitude,
            longitude=result.longitude,
            address=result.address,
            city=result.city,
            country=result.country,
        )
        for result in results
    ]
