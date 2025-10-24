"""API tests for geocoding endpoints."""

import pytest

from app.services.geocoding_service import GeocodingResult, GeocodingService, get_geocoding_service
from main import app


class MockGeocodingService(GeocodingService):
    """Mock geocoding service for testing without actual API calls."""

    def __init__(self):
        """Initialize without calling the parent constructor."""
        # Don't call super().__init__() to avoid creating real geolocator
        pass

    def reverse_geocode(self, latitude: float, longitude: float) -> GeocodingResult | None:
        """Return mock reverse geocoding results."""
        # Mock data for specific test coordinates
        if latitude == 40.7128 and longitude == -74.0060:
            return GeocodingResult(
                latitude=40.7128,
                longitude=-74.0060,
                address="New York City Hall, 260, Broadway, Manhattan, New York, 10007, USA",
                city="New York",
                country="United States",
            )
        elif latitude == 51.5074 and longitude == -0.1278:
            return GeocodingResult(
                latitude=51.5074,
                longitude=-0.1278,
                address="Westminster, London, England, United Kingdom",
                city="London",
                country="United Kingdom",
            )
        elif latitude == 48.8566 and longitude == 2.3522:
            return GeocodingResult(
                latitude=48.8566,
                longitude=2.3522,
                address="Paris, Île-de-France, France",
                city="Paris",
                country="France",
            )
        else:
            # Return None for unknown coordinates
            return None

    def search_address(self, query: str, limit: int = 5) -> list[GeocodingResult]:
        """Return mock search results."""
        query_lower = query.lower()

        if "new york" in query_lower:
            return [
                GeocodingResult(
                    latitude=40.7128,
                    longitude=-74.0060,
                    address="New York, NY, USA",
                    city="New York",
                    country="United States",
                ),
                GeocodingResult(
                    latitude=43.0481,
                    longitude=-76.1474,
                    address="New York, USA",
                    city="New York",
                    country="United States",
                ),
            ][:limit]
        elif "london" in query_lower:
            return [
                GeocodingResult(
                    latitude=51.5074,
                    longitude=-0.1278,
                    address="London, England, United Kingdom",
                    city="London",
                    country="United Kingdom",
                )
            ][:limit]
        elif "paris" in query_lower:
            return [
                GeocodingResult(
                    latitude=48.8566,
                    longitude=2.3522,
                    address="Paris, Île-de-France, France",
                    city="Paris",
                    country="France",
                ),
                GeocodingResult(
                    latitude=48.8567,
                    longitude=2.3508,
                    address="Paris, Texas, USA",
                    city="Paris",
                    country="United States",
                ),
            ][:limit]
        else:
            return []


@pytest.fixture
def client_with_mock_geocoding(client):
    """Override geocoding service with mock implementation."""
    mock_service = MockGeocodingService()
    app.dependency_overrides[get_geocoding_service] = lambda: mock_service

    try:
        yield client
    finally:
        app.dependency_overrides.pop(get_geocoding_service, None)


def test_reverse_geocode_new_york(client_with_mock_geocoding):
    """API can reverse geocode New York City coordinates."""
    # Act
    response = client_with_mock_geocoding.get(
        "/api/v1/geocoding/reverse",
        params={"latitude": 40.7128, "longitude": -74.0060},
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["latitude"] == 40.7128
    assert data["longitude"] == -74.0060
    assert data["city"] == "New York"
    assert data["country"] == "United States"
    assert "New York" in data["address"]


def test_reverse_geocode_london(client_with_mock_geocoding):
    """API can reverse geocode London coordinates."""
    # Act
    response = client_with_mock_geocoding.get(
        "/api/v1/geocoding/reverse",
        params={"latitude": 51.5074, "longitude": -0.1278},
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["latitude"] == 51.5074
    assert data["longitude"] == -0.1278
    assert data["city"] == "London"
    assert data["country"] == "United Kingdom"


def test_reverse_geocode_paris(client_with_mock_geocoding):
    """API can reverse geocode Paris coordinates."""
    # Act
    response = client_with_mock_geocoding.get(
        "/api/v1/geocoding/reverse",
        params={"latitude": 48.8566, "longitude": 2.3522},
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["latitude"] == 48.8566
    assert data["longitude"] == 2.3522
    assert data["city"] == "Paris"
    assert data["country"] == "France"


def test_reverse_geocode_not_found(client_with_mock_geocoding):
    """API returns 404 when coordinates cannot be reverse geocoded."""
    # Act
    response = client_with_mock_geocoding.get(
        "/api/v1/geocoding/reverse",
        params={"latitude": 0.0, "longitude": 0.0},
    )

    # Assert
    assert response.status_code == 404
    data = response.json()
    assert "Could not find address" in data["detail"]


def test_reverse_geocode_invalid_latitude(client_with_mock_geocoding):
    """API validates latitude is within valid range."""
    # Act
    response = client_with_mock_geocoding.get(
        "/api/v1/geocoding/reverse",
        params={"latitude": 91.0, "longitude": 0.0},
    )

    # Assert
    assert response.status_code == 422


def test_reverse_geocode_invalid_longitude(client_with_mock_geocoding):
    """API validates longitude is within valid range."""
    # Act
    response = client_with_mock_geocoding.get(
        "/api/v1/geocoding/reverse",
        params={"latitude": 0.0, "longitude": 181.0},
    )

    # Assert
    assert response.status_code == 422


def test_reverse_geocode_missing_parameters(client_with_mock_geocoding):
    """API requires both latitude and longitude parameters."""
    # Act
    response = client_with_mock_geocoding.get(
        "/api/v1/geocoding/reverse",
        params={"latitude": 40.7128},
    )

    # Assert
    assert response.status_code == 422


def test_search_address_new_york(client_with_mock_geocoding):
    """API can search for New York locations."""
    # Act
    response = client_with_mock_geocoding.get(
        "/api/v1/geocoding/search",
        params={"q": "New York"},
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["city"] == "New York"
    assert data[0]["country"] == "United States"
    assert data[0]["latitude"] == 40.7128
    assert data[0]["longitude"] == -74.0060


def test_search_address_london(client_with_mock_geocoding):
    """API can search for London locations."""
    # Act
    response = client_with_mock_geocoding.get(
        "/api/v1/geocoding/search",
        params={"q": "London"},
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["city"] == "London"
    assert data[0]["country"] == "United Kingdom"


def test_search_address_paris_with_limit(client_with_mock_geocoding):
    """API respects the limit parameter in search."""
    # Act
    response = client_with_mock_geocoding.get(
        "/api/v1/geocoding/search",
        params={"q": "Paris", "limit": 1},
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["city"] == "Paris"


def test_search_address_default_limit(client_with_mock_geocoding):
    """API uses default limit when not specified."""
    # Act
    response = client_with_mock_geocoding.get(
        "/api/v1/geocoding/search",
        params={"q": "Paris"},
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2  # Mock returns 2 results for Paris


def test_search_address_no_results(client_with_mock_geocoding):
    """API returns empty list when search finds nothing."""
    # Act
    response = client_with_mock_geocoding.get(
        "/api/v1/geocoding/search",
        params={"q": "NonexistentPlace12345"},
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data == []


def test_search_address_empty_query(client_with_mock_geocoding):
    """API validates query has minimum length."""
    # Act
    response = client_with_mock_geocoding.get(
        "/api/v1/geocoding/search",
        params={"q": ""},
    )

    # Assert
    assert response.status_code == 422


def test_search_address_missing_query(client_with_mock_geocoding):
    """API requires query parameter."""
    # Act
    response = client_with_mock_geocoding.get("/api/v1/geocoding/search")

    # Assert
    assert response.status_code == 422


def test_search_address_limit_validation(client_with_mock_geocoding):
    """API validates limit is within allowed range."""
    # Act - limit too high
    response = client_with_mock_geocoding.get(
        "/api/v1/geocoding/search",
        params={"q": "London", "limit": 11},
    )

    # Assert
    assert response.status_code == 422


def test_search_address_limit_minimum(client_with_mock_geocoding):
    """API validates limit is at least 1."""
    # Act
    response = client_with_mock_geocoding.get(
        "/api/v1/geocoding/search",
        params={"q": "London", "limit": 0},
    )

    # Assert
    assert response.status_code == 422


def test_reverse_geocode_returns_json(client_with_mock_geocoding):
    """API returns proper JSON response structure."""
    # Act
    response = client_with_mock_geocoding.get(
        "/api/v1/geocoding/reverse",
        params={"latitude": 40.7128, "longitude": -74.0060},
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "latitude" in data
    assert "longitude" in data
    assert "address" in data
    assert "city" in data
    assert "country" in data


def test_search_returns_json_array(client_with_mock_geocoding):
    """API returns array of location objects."""
    # Act
    response = client_with_mock_geocoding.get(
        "/api/v1/geocoding/search",
        params={"q": "New York"},
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "latitude" in data[0]
        assert "longitude" in data[0]
        assert "address" in data[0]
        assert "city" in data[0]
        assert "country" in data[0]
