"""Geocoding service for converting between addresses and coordinates."""

from __future__ import annotations

from typing import NamedTuple

from geopy.exc import GeopyError
from geopy.geocoders import Nominatim

from app.core.config import get_settings


class GeocodingResult(NamedTuple):
    """Result from a geocoding operation."""

    latitude: float
    longitude: float
    address: str | None = None
    city: str | None = None
    country: str | None = None


class GeocodingService:
    """Service for geocoding operations using Nominatim (OpenStreetMap)."""

    def __init__(self, user_agent: str | None = None):
        """Initialize the geocoding service.

        Args:
            user_agent: User agent string for API requests. If None, uses value from settings.
        """
        if user_agent is None:
            user_agent = get_settings().geocoding_user_agent
        self.geolocator = Nominatim(user_agent=user_agent)

    @staticmethod
    def _extract_city(address_parts: dict) -> str | None:
        """Extract city name from address components.

        Tries multiple fields in order of preference: city, town, village, municipality, county.

        Args:
            address_parts: Address dictionary from Nominatim response

        Returns:
            City name if found, None otherwise
        """
        return (
            address_parts.get("city")
            or address_parts.get("town")
            or address_parts.get("village")
            or address_parts.get("municipality")
            or address_parts.get("county")
        )

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
            city = self._extract_city(address_parts)
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
                city = self._extract_city(address_parts)
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
