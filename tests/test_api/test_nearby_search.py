"""Tests for nearby skate spot search with geocoding fallback."""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.models.skate_spot import Difficulty, SpotType
from app.services.geocoding_service import GeocodingResult, get_geocoding_service
from main import app


class StubGeocodingService:
    """Simple geocoder stub that always returns a fixed result."""

    def __init__(self, result: GeocodingResult):
        self._result = result

    def search_address(self, query: str, limit: int = 5) -> list[GeocodingResult]:  # noqa: ARG002
        return [self._result]


@pytest.fixture
def stub_geocoder():
    """Provide a stubbed geocoder and clean up the override."""
    result = GeocodingResult(
        latitude=37.7749,
        longitude=-122.4194,
        address="Test City",
        city="Test City",
        country="Testland",
    )
    app.dependency_overrides[get_geocoding_service] = lambda: StubGeocodingService(result)
    try:
        yield result
    finally:
        app.dependency_overrides.pop(get_geocoding_service, None)


def test_nearby_allows_location_query_without_coordinates(client, auth_token, stub_geocoder):
    """Location strings are geocoded when latitude/longitude are omitted."""
    response = client.post(
        "/api/v1/skate-spots/",
        json={
            "name": "Mission Plaza",
            "description": "Manual pads by the theater",
            "spot_type": SpotType.STREET.value,
            "difficulty": Difficulty.INTERMEDIATE.value,
            "location": {
                "latitude": stub_geocoder.latitude,
                "longitude": stub_geocoder.longitude,
                "city": "San Francisco",
                "country": "USA",
            },
            "is_public": True,
        },
        cookies={"access_token": auth_token},
    )
    spot_id = response.json()["id"]

    nearby = client.get(
        "/api/v1/skate-spots/nearby",
        params={"location": "Test City", "radius_km": 10},
    )

    assert nearby.status_code == 200
    payload = nearby.json()
    assert payload
    assert payload[0]["id"] == spot_id
    assert payload[0]["distance_km"] is not None


def test_nearby_rejects_partial_coordinates(client):
    """Both coordinates must be supplied together when using explicit values."""
    response = client.get(
        "/api/v1/skate-spots/nearby",
        params={"latitude": 10.0, "radius_km": 5, "search": str(uuid4())},
    )

    assert response.status_code == 422
