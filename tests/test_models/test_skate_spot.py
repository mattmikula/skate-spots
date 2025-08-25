"""Tests for skate spot models."""

import pytest
from pydantic import ValidationError

from app.models.skate_spot import (
    Difficulty,
    Location,
    SkateSpot,
    SkateSpotCreate,
    SkateSpotUpdate,
    SpotType,
)


# Location model tests
def test_valid_location():
    """Test creating a valid location."""
    location_data = {
        "latitude": 40.7128,
        "longitude": -74.0060,
        "address": "123 Main St",
        "city": "New York",
        "country": "USA",
    }
    location = Location(**location_data)
    assert location.latitude == 40.7128
    assert location.longitude == -74.0060
    assert location.city == "New York"


def test_location_without_address():
    """Test creating location without optional address."""
    location_data = {
        "latitude": 40.7128,
        "longitude": -74.0060,
        "city": "New York",
        "country": "USA",
    }
    location = Location(**location_data)
    assert location.address is None


def test_invalid_latitude_too_high():
    """Test latitude validation for values too high."""
    with pytest.raises(ValidationError) as exc_info:
        Location(
            latitude=91.0,  # Invalid: > 90
            longitude=-74.0060,
            city="New York",
            country="USA",
        )
    assert "less than or equal to 90" in str(exc_info.value)


def test_invalid_latitude_too_low():
    """Test latitude validation for values too low."""
    with pytest.raises(ValidationError) as exc_info:
        Location(
            latitude=-91.0,  # Invalid: < -90
            longitude=-74.0060,
            city="New York",
            country="USA",
        )
    assert "greater than or equal to -90" in str(exc_info.value)


def test_invalid_longitude_too_high():
    """Test longitude validation for values too high."""
    with pytest.raises(ValidationError) as exc_info:
        Location(
            latitude=40.7128,
            longitude=181.0,  # Invalid: > 180
            city="New York",
            country="USA",
        )
    assert "less than or equal to 180" in str(exc_info.value)


def test_empty_city_validation():
    """Test city cannot be empty."""
    with pytest.raises(ValidationError) as exc_info:
        Location(
            latitude=40.7128,
            longitude=-74.0060,
            city="",  # Invalid: empty string
            country="USA",
        )
    assert "at least 1 character" in str(exc_info.value)


# SkateSpotCreate model tests
def test_valid_skate_spot_create():
    """Test creating a valid skate spot."""
    spot_data = {
        "name": "Downtown Rails",
        "description": "Great rails for grinding",
        "spot_type": SpotType.RAIL,
        "difficulty": Difficulty.INTERMEDIATE,
        "location": {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "city": "New York",
            "country": "USA",
        },
        "is_public": True,
        "requires_permission": False,
    }
    spot = SkateSpotCreate(**spot_data)
    assert spot.name == "Downtown Rails"
    assert spot.spot_type == SpotType.RAIL
    assert spot.difficulty == Difficulty.INTERMEDIATE


def test_name_empty_validation():
    """Test that empty name fails validation."""
    base_data = {
        "description": "Great rails for grinding",
        "spot_type": SpotType.RAIL,
        "difficulty": Difficulty.INTERMEDIATE,
        "location": {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "city": "New York",
            "country": "USA",
        },
    }

    with pytest.raises(ValidationError):
        SkateSpotCreate(name="", **base_data)


def test_name_too_long_validation():
    """Test that name too long fails validation."""
    base_data = {
        "description": "Great rails for grinding",
        "spot_type": SpotType.RAIL,
        "difficulty": Difficulty.INTERMEDIATE,
        "location": {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "city": "New York",
            "country": "USA",
        },
    }

    with pytest.raises(ValidationError):
        SkateSpotCreate(name="x" * 101, **base_data)


def test_name_valid_length():
    """Test that valid length name passes validation."""
    base_data = {
        "description": "Great rails for grinding",
        "spot_type": SpotType.RAIL,
        "difficulty": Difficulty.INTERMEDIATE,
        "location": {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "city": "New York",
            "country": "USA",
        },
    }

    spot = SkateSpotCreate(name="Valid Name", **base_data)
    assert spot.name == "Valid Name"


def test_description_empty_validation():
    """Test that empty description fails validation."""
    base_data = {
        "name": "Test Spot",
        "spot_type": SpotType.RAIL,
        "difficulty": Difficulty.INTERMEDIATE,
        "location": {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "city": "New York",
            "country": "USA",
        },
    }

    with pytest.raises(ValidationError):
        SkateSpotCreate(description="", **base_data)


def test_description_too_long_validation():
    """Test that description too long fails validation."""
    base_data = {
        "name": "Test Spot",
        "spot_type": SpotType.RAIL,
        "difficulty": Difficulty.INTERMEDIATE,
        "location": {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "city": "New York",
            "country": "USA",
        },
    }

    with pytest.raises(ValidationError):
        SkateSpotCreate(description="x" * 1001, **base_data)


def test_valid_spot_type_enum():
    """Test that valid spot type enum passes validation."""
    base_data = {
        "name": "Test Spot",
        "description": "Test description",
        "difficulty": Difficulty.BEGINNER,
        "location": {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "city": "New York",
            "country": "USA",
        },
    }

    spot = SkateSpotCreate(spot_type=SpotType.PARK, **base_data)
    assert spot.spot_type == SpotType.PARK


def test_valid_difficulty_enum():
    """Test that valid difficulty enum passes validation."""
    base_data = {
        "name": "Test Spot",
        "description": "Test description",
        "spot_type": SpotType.PARK,
        "location": {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "city": "New York",
            "country": "USA",
        },
    }

    spot = SkateSpotCreate(difficulty=Difficulty.BEGINNER, **base_data)
    assert spot.difficulty == Difficulty.BEGINNER


def test_invalid_spot_type_enum():
    """Test that invalid spot_type fails validation."""
    base_data = {
        "name": "Test Spot",
        "description": "Test description",
        "difficulty": Difficulty.BEGINNER,
        "location": {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "city": "New York",
            "country": "USA",
        },
    }

    with pytest.raises(ValidationError):
        SkateSpotCreate(spot_type="invalid_type", **base_data)


# SkateSpotUpdate model tests
def test_all_fields_optional():
    """Test that all fields are optional in update model."""
    update = SkateSpotUpdate()
    assert update.name is None
    assert update.description is None
    assert update.spot_type is None


def test_partial_update():
    """Test updating only some fields."""
    update = SkateSpotUpdate(
        name="Updated Name",
        difficulty=Difficulty.ADVANCED,
    )
    assert update.name == "Updated Name"
    assert update.difficulty == Difficulty.ADVANCED
    assert update.description is None


def test_update_name_empty_validation():
    """Test that empty name still fails validation in update."""
    with pytest.raises(ValidationError):
        SkateSpotUpdate(name="")


def test_update_name_too_long_validation():
    """Test that name too long still fails validation in update."""
    with pytest.raises(ValidationError):
        SkateSpotUpdate(name="x" * 101)


# Complete SkateSpot model tests
def test_auto_generated_fields():
    """Test that ID and timestamps are auto-generated."""
    spot_data = {
        "name": "Test Spot",
        "description": "Test description",
        "spot_type": SpotType.RAIL,
        "difficulty": Difficulty.INTERMEDIATE,
        "location": Location(
            latitude=40.7128,
            longitude=-74.0060,
            city="New York",
            country="USA",
        ),
    }
    spot = SkateSpot(**spot_data)

    assert spot.id is not None
    assert spot.created_at is not None
    assert spot.updated_at is not None
    # Timestamps should be close but may have microsecond differences
    time_diff = abs((spot.updated_at - spot.created_at).total_seconds())
    assert time_diff < 0.1  # Within 100ms


def test_default_values():
    """Test default values for boolean fields."""
    spot_data = {
        "name": "Test Spot",
        "description": "Test description",
        "spot_type": SpotType.RAIL,
        "difficulty": Difficulty.INTERMEDIATE,
        "location": Location(
            latitude=40.7128,
            longitude=-74.0060,
            city="New York",
            country="USA",
        ),
    }
    spot = SkateSpot(**spot_data)

    assert spot.is_public is True  # Default value
    assert spot.requires_permission is False  # Default value
