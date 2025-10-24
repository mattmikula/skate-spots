"""Geocoding service for converting between addresses and coordinates."""

from __future__ import annotations

from typing import NamedTuple

from geopy.exc import GeopyError
from geopy.geocoders import Nominatim


class GeocodingResult(NamedTuple):
    """Result from a geocoding operation."""

    latitude: float
    longitude: float
    address: str | None = None
    city: str | None = None
    country: str | None = None


class GeocodingService:
    """Service for geocoding operations using Nominatim (OpenStreetMap)."""

    def __init__(self):
        """Initialize the geocoding service."""
        self.geolocator = Nominatim(user_agent="skate-spots-app")

    def reverse_geocode(self, latitude: float, longitude: float) -> GeocodingResult | None:
        """
        Convert coordinates to address information.

        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate

        Returns:
            GeocodingResult with address information or None if not found
        """
        try:
            location = self.geolocator.reverse((latitude, longitude), language="en")
            if not location:
                return None

            address_parts = location.raw.get("address", {})

            # Try to extract city from various possible fields
            city = (
                address_parts.get("city")
                or address_parts.get("town")
                or address_parts.get("village")
                or address_parts.get("municipality")
                or address_parts.get("county")
            )

            country = address_parts.get("country")
            display_address = location.address

            return GeocodingResult(
                latitude=latitude,
                longitude=longitude,
                address=display_address,
                city=city,
                country=country,
            )
        except GeopyError:
            return None

    def search_address(self, query: str, limit: int = 5) -> list[GeocodingResult]:
        """
        Search for locations matching a query string.

        Args:
            query: Search query (address, place name, etc.)
            limit: Maximum number of results to return

        Returns:
            List of GeocodingResult objects
        """
        try:
            locations = self.geolocator.geocode(query, exactly_one=False, limit=limit)
            if not locations:
                return []

            results = []
            for location in locations:
                address_parts = location.raw.get("address", {})

                # Try to extract city from various possible fields
                city = (
                    address_parts.get("city")
                    or address_parts.get("town")
                    or address_parts.get("village")
                    or address_parts.get("municipality")
                    or address_parts.get("county")
                )

                country = address_parts.get("country")

                results.append(
                    GeocodingResult(
                        latitude=location.latitude,
                        longitude=location.longitude,
                        address=location.address,
                        city=city,
                        country=country,
                    )
                )

            return results
        except GeopyError:
            return []


def get_geocoding_service() -> GeocodingService:
    """Provide the geocoding service for dependency injection."""
    return GeocodingService()
