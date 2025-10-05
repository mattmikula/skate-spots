"""Tests for skate spots API endpoints."""

from uuid import uuid4

import pytest

from app.models.skate_spot import Difficulty, SpotType


@pytest.fixture
def sample_spot_payload():
    """Sample payload for creating a skate spot."""
    return {
        "name": "API Test Spot",
        "description": "A spot for testing the API endpoints",
        "spot_type": SpotType.RAIL.value,
        "difficulty": Difficulty.INTERMEDIATE.value,
        "location": {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "address": "123 Test St",
            "city": "New York",
            "country": "USA",
        },
        "is_public": True,
        "requires_permission": False,
    }


@pytest.fixture
def created_spot_id(client, sample_spot_payload):
    """Create a spot and return its ID for testing."""
    response = client.post("/api/v1/skate-spots/", json=sample_spot_payload)
    return response.json()["id"]


@pytest.fixture
def second_spot_id(client, sample_spot_payload):
    """Create a second spot and return its ID for testing."""
    second_payload = sample_spot_payload.copy()
    second_payload["name"] = "Second Spot"
    response = client.post("/api/v1/skate-spots/", json=second_payload)
    return response.json()["id"]


@pytest.fixture
def deleted_spot_id(client, sample_spot_payload):
    """Create a spot, delete it, and return its ID for testing."""
    # Create spot
    response = client.post("/api/v1/skate-spots/", json=sample_spot_payload)
    spot_id = response.json()["id"]
    # Delete it
    client.delete(f"/api/v1/skate-spots/{spot_id}")
    return spot_id


# Create tests
def test_create_spot(client, sample_spot_payload):
    """Test creating a new spot."""
    response = client.post("/api/v1/skate-spots/", json=sample_spot_payload)

    assert response.status_code == 201
    data = response.json()

    # Check all fields are present and correct
    assert data["name"] == "API Test Spot"
    assert data["description"] == "A spot for testing the API endpoints"
    assert data["spot_type"] == "rail"
    assert data["difficulty"] == "intermediate"
    assert data["is_public"] is True
    assert data["requires_permission"] is False

    # Check generated fields
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data

    # Check location
    location = data["location"]
    assert location["latitude"] == 40.7128
    assert location["longitude"] == -74.0060
    assert location["city"] == "New York"


def test_create_spot_invalid_data(client):
    """Test creating a spot with invalid data."""
    invalid_payload = {
        "name": "",  # Invalid: empty name
        "description": "Test description",
        "spot_type": "invalid_type",  # Invalid: not in enum
        "difficulty": "beginner",
        "location": {
            "latitude": 91.0,  # Invalid: > 90
            "longitude": -74.0060,
            "city": "New York",
            "country": "USA",
        },
    }

    response = client.post("/api/v1/skate-spots/", json=invalid_payload)
    assert response.status_code == 422  # Validation error


# Read tests
def test_list_empty_spots(client):
    """Test listing spots when none exist."""
    response = client.get("/api/v1/skate-spots/")
    assert response.status_code == 200
    assert response.json() == []


def test_get_spot_by_id(client, created_spot_id):
    """Test getting a specific spot by ID."""
    get_response = client.get(f"/api/v1/skate-spots/{created_spot_id}")
    assert get_response.status_code == 200

    retrieved_spot = get_response.json()
    assert retrieved_spot["id"] == created_spot_id
    assert retrieved_spot["name"] == "API Test Spot"


def test_get_nonexistent_spot(client):
    """Test getting a spot that doesn't exist."""
    fake_id = str(uuid4())
    response = client.get(f"/api/v1/skate-spots/{fake_id}")

    assert response.status_code == 404
    assert f"Skate spot with id {fake_id} not found" in response.json()["detail"]


def test_get_spot_invalid_uuid(client):
    """Test getting a spot with invalid UUID format."""
    response = client.get("/api/v1/skate-spots/not-a-uuid")
    assert response.status_code == 422  # Validation error


def test_list_spots_with_existing_data(client, created_spot_id, second_spot_id):
    """Test listing spots when spots exist."""
    response = client.get("/api/v1/skate-spots/")
    assert response.status_code == 200

    spots = response.json()
    assert len(spots) == 2
    spot_ids = [spot["id"] for spot in spots]
    assert created_spot_id in spot_ids
    assert second_spot_id in spot_ids


# Update tests
def test_update_spot(client, created_spot_id):
    """Test updating an existing spot."""
    update_payload = {
        "name": "Updated Spot Name",
        "difficulty": "advanced",
    }

    update_response = client.put(f"/api/v1/skate-spots/{created_spot_id}", json=update_payload)
    assert update_response.status_code == 200

    updated_spot = update_response.json()
    assert updated_spot["name"] == "Updated Spot Name"
    assert updated_spot["difficulty"] == "advanced"
    # Verify the spot was actually updated
    assert updated_spot["id"] == created_spot_id


def test_update_nonexistent_spot(client):
    """Test updating a spot that doesn't exist."""
    fake_id = str(uuid4())
    update_payload = {"name": "Won't work"}

    response = client.put(f"/api/v1/skate-spots/{fake_id}", json=update_payload)
    assert response.status_code == 404
    assert f"Skate spot with id {fake_id} not found" in response.json()["detail"]


def test_update_spot_invalid_data(client, created_spot_id):
    """Test updating with invalid data."""
    invalid_update = {
        "name": "",  # Invalid: empty name
        "difficulty": "invalid_difficulty",  # Invalid: not in enum
    }

    response = client.put(f"/api/v1/skate-spots/{created_spot_id}", json=invalid_update)
    assert response.status_code == 422  # Validation error


# Delete tests
def test_delete_spot(client, created_spot_id):
    """Test deleting an existing spot."""
    delete_response = client.delete(f"/api/v1/skate-spots/{created_spot_id}")
    assert delete_response.status_code == 204


def test_get_deleted_spot_returns_404(client, deleted_spot_id):
    """Test that getting a deleted spot returns 404."""
    get_response = client.get(f"/api/v1/skate-spots/{deleted_spot_id}")
    assert get_response.status_code == 404


def test_delete_nonexistent_spot(client):
    """Test deleting a spot that doesn't exist."""
    fake_id = str(uuid4())
    response = client.delete(f"/api/v1/skate-spots/{fake_id}")

    assert response.status_code == 404
    assert f"Skate spot with id {fake_id} not found" in response.json()["detail"]
