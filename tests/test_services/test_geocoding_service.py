"""Tests for the geocoding service."""

from unittest.mock import MagicMock, Mock

import pytest
from geopy.exc import GeopyError

from app.services.geocoding_service import GeocodingResult, GeocodingService


@pytest.fixture
def mock_geolocator():
    """Create a mock geolocator for testing."""
    return MagicMock()


@pytest.fixture
def geocoding_service(mock_geolocator):
    """Create a geocoding service with a mocked geolocator."""
    service = GeocodingService()
    service.geolocator = mock_geolocator
    return service


def test_reverse_geocode_success(geocoding_service, mock_geolocator):
    """Service can reverse geocode coordinates to address information."""
    # Arrange
    mock_location = Mock()
    mock_location.address = "123 Main St, New York, NY 10001, USA"
    mock_location.raw = {
        "address": {
            "city": "New York",
            "country": "United States",
        }
    }
    mock_geolocator.reverse.return_value = mock_location

    # Act
    result = geocoding_service.reverse_geocode(40.7128, -74.0060)

    # Assert
    assert result is not None
    assert isinstance(result, GeocodingResult)
    assert result.latitude == 40.7128
    assert result.longitude == -74.0060
    assert result.city == "New York"
    assert result.country == "United States"
    assert result.address == "123 Main St, New York, NY 10001, USA"
    mock_geolocator.reverse.assert_called_once_with((40.7128, -74.0060), language="en")


def test_reverse_geocode_extracts_city_from_town(geocoding_service, mock_geolocator):
    """Service can extract city from 'town' field when 'city' is not available."""
    # Arrange
    mock_location = Mock()
    mock_location.address = "456 Oak St, Springfield, IL 62701, USA"
    mock_location.raw = {
        "address": {
            "town": "Springfield",
            "country": "United States",
        }
    }
    mock_geolocator.reverse.return_value = mock_location

    # Act
    result = geocoding_service.reverse_geocode(39.7817, -89.6501)

    # Assert
    assert result is not None
    assert result.city == "Springfield"


def test_reverse_geocode_extracts_city_from_village(geocoding_service, mock_geolocator):
    """Service can extract city from 'village' field when city/town not available."""
    # Arrange
    mock_location = Mock()
    mock_location.address = "Rural Road, Small Village, Country"
    mock_location.raw = {
        "address": {
            "village": "Small Village",
            "country": "Country",
        }
    }
    mock_geolocator.reverse.return_value = mock_location

    # Act
    result = geocoding_service.reverse_geocode(50.0, 10.0)

    # Assert
    assert result is not None
    assert result.city == "Small Village"


def test_reverse_geocode_not_found(geocoding_service, mock_geolocator):
    """Service returns None when reverse geocoding fails to find a location."""
    # Arrange
    mock_geolocator.reverse.return_value = None

    # Act
    result = geocoding_service.reverse_geocode(0.0, 0.0)

    # Assert
    assert result is None


def test_reverse_geocode_handles_geopy_error(geocoding_service, mock_geolocator):
    """Service gracefully handles GeoPy errors and returns None."""
    # Arrange
    mock_geolocator.reverse.side_effect = GeopyError("Service unavailable")

    # Act
    result = geocoding_service.reverse_geocode(40.7128, -74.0060)

    # Assert
    assert result is None


def test_search_address_success(geocoding_service, mock_geolocator):
    """Service can search for locations matching a query."""
    # Arrange
    mock_location1 = Mock()
    mock_location1.latitude = 40.7128
    mock_location1.longitude = -74.0060
    mock_location1.address = "New York City, NY, USA"
    mock_location1.raw = {
        "address": {
            "city": "New York",
            "country": "United States",
        }
    }

    mock_location2 = Mock()
    mock_location2.latitude = 43.0481
    mock_location2.longitude = -76.1474
    mock_location2.address = "New York, USA"
    mock_location2.raw = {
        "address": {
            "town": "New York",
            "country": "United States",
        }
    }

    mock_geolocator.geocode.return_value = [mock_location1, mock_location2]

    # Act
    results = geocoding_service.search_address("New York", limit=2)

    # Assert
    assert len(results) == 2
    assert isinstance(results[0], GeocodingResult)
    assert results[0].latitude == 40.7128
    assert results[0].longitude == -74.0060
    assert results[0].city == "New York"
    assert results[0].country == "United States"
    assert results[1].city == "New York"
    mock_geolocator.geocode.assert_called_once_with("New York", exactly_one=False, limit=2)


def test_search_address_no_results(geocoding_service, mock_geolocator):
    """Service returns empty list when search finds no results."""
    # Arrange
    mock_geolocator.geocode.return_value = None

    # Act
    results = geocoding_service.search_address("NonexistentPlace12345")

    # Assert
    assert results == []


def test_search_address_handles_geopy_error(geocoding_service, mock_geolocator):
    """Service gracefully handles GeoPy errors and returns empty list."""
    # Arrange
    mock_geolocator.geocode.side_effect = GeopyError("Rate limit exceeded")

    # Act
    results = geocoding_service.search_address("New York")

    # Assert
    assert results == []


def test_search_address_default_limit(geocoding_service, mock_geolocator):
    """Service uses default limit of 5 when not specified."""
    # Arrange
    mock_geolocator.geocode.return_value = []

    # Act
    geocoding_service.search_address("Test Query")

    # Assert
    mock_geolocator.geocode.assert_called_once_with("Test Query", exactly_one=False, limit=5)


def test_geocoding_result_namedtuple():
    """GeocodingResult is a proper NamedTuple with expected fields."""
    # Act
    result = GeocodingResult(
        latitude=40.7128,
        longitude=-74.0060,
        address="123 Main St",
        city="New York",
        country="USA",
    )

    # Assert
    assert result.latitude == 40.7128
    assert result.longitude == -74.0060
    assert result.address == "123 Main St"
    assert result.city == "New York"
    assert result.country == "USA"


def test_geocoding_result_optional_fields():
    """GeocodingResult allows None for optional fields."""
    # Act
    result = GeocodingResult(latitude=40.7128, longitude=-74.0060)

    # Assert
    assert result.latitude == 40.7128
    assert result.longitude == -74.0060
    assert result.address is None
    assert result.city is None
    assert result.country is None
