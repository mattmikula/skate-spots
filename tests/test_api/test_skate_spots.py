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
def created_spot_id(client, sample_spot_payload, auth_token):
    """Create a spot and return its ID for testing."""
    response = client.post(
        "/api/v1/skate-spots/",
        json=sample_spot_payload,
        cookies={"access_token": auth_token},
    )
    return response.json()["id"]


@pytest.fixture
def second_spot_id(client, sample_spot_payload, auth_token):
    """Create a second spot and return its ID for testing."""
    second_payload = sample_spot_payload.copy()
    second_payload["name"] = "Second Spot"
    response = client.post(
        "/api/v1/skate-spots/",
        json=second_payload,
        cookies={"access_token": auth_token},
    )
    return response.json()["id"]


@pytest.fixture
def deleted_spot_id(client, sample_spot_payload, auth_token):
    """Create a spot, delete it, and return its ID for testing."""
    # Create spot
    response = client.post(
        "/api/v1/skate-spots/",
        json=sample_spot_payload,
        cookies={"access_token": auth_token},
    )
    spot_id = response.json()["id"]
    # Delete it
    client.delete(f"/api/v1/skate-spots/{spot_id}", cookies={"access_token": auth_token})
    return spot_id


# Create tests
def test_create_spot(client, sample_spot_payload, auth_token):
    """Test creating a new spot."""
    response = client.post(
        "/api/v1/skate-spots/",
        json=sample_spot_payload,
        cookies={"access_token": auth_token},
    )

    assert response.status_code == 201
    data = response.json()

    # Check all fields are present and correct
    assert data["name"] == "API Test Spot"
    assert data["description"] == "A spot for testing the API endpoints"
    assert data["spot_type"] == "rail"
    assert data["difficulty"] == "intermediate"
    assert data["is_public"] is True
    assert data["requires_permission"] is False
    assert data["average_rating"] is None
    assert data["ratings_count"] == 0

    # Check generated fields
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data

    # Check location
    location = data["location"]
    assert location["latitude"] == 40.7128
    assert location["longitude"] == -74.0060
    assert location["city"] == "New York"


def test_create_spot_invalid_data(client, auth_token):
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

    response = client.post(
        "/api/v1/skate-spots/",
        json=invalid_payload,
        cookies={"access_token": auth_token},
    )
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
    assert retrieved_spot["average_rating"] is None
    assert retrieved_spot["ratings_count"] == 0


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
    for spot in spots:
        assert "average_rating" in spot
        assert "ratings_count" in spot


def test_list_spots_with_filters(client, sample_spot_payload, auth_token):
    """Query parameters filter the skate spot collection."""

    client.post(
        "/api/v1/skate-spots/",
        json=sample_spot_payload,
        cookies={"access_token": auth_token},
    )

    advanced_payload = sample_spot_payload.copy()
    advanced_payload["name"] = "Advanced Bowl"
    advanced_payload["description"] = "Deep bowl requiring permission"
    advanced_payload["spot_type"] = SpotType.BOWL.value
    advanced_payload["difficulty"] = Difficulty.ADVANCED.value
    advanced_payload["is_public"] = False
    advanced_payload["requires_permission"] = True
    advanced_payload["location"] = {
        **sample_spot_payload["location"],
        "city": "Los Angeles",
    }

    client.post(
        "/api/v1/skate-spots/",
        json=advanced_payload,
        cookies={"access_token": auth_token},
    )

    difficulty_response = client.get(
        "/api/v1/skate-spots/",
        params={"difficulty": Difficulty.ADVANCED.value},
    )
    assert difficulty_response.status_code == 200
    filtered = difficulty_response.json()
    assert len(filtered) == 1
    assert filtered[0]["name"] == "Advanced Bowl"

    search_response = client.get(
        "/api/v1/skate-spots/",
        params={"search": "los"},
    )
    assert search_response.status_code == 200
    search_results = search_response.json()
    assert len(search_results) == 1
    assert search_results[0]["name"] == "Advanced Bowl"

    permissions_response = client.get(
        "/api/v1/skate-spots/",
        params={"requires_permission": "true", "is_public": "false"},
    )
    assert permissions_response.status_code == 200
    permission_results = permissions_response.json()
    assert len(permission_results) == 1
    assert permission_results[0]["name"] == "Advanced Bowl"


# Update tests
def test_update_spot(client, created_spot_id, auth_token):
    """Test updating an existing spot."""
    update_payload = {
        "name": "Updated Spot Name",
        "difficulty": "advanced",
    }

    update_response = client.put(
        f"/api/v1/skate-spots/{created_spot_id}",
        json=update_payload,
        cookies={"access_token": auth_token},
    )
    assert update_response.status_code == 200

    updated_spot = update_response.json()
    assert updated_spot["name"] == "Updated Spot Name"
    assert updated_spot["difficulty"] == "advanced"
    # Verify the spot was actually updated
    assert updated_spot["id"] == created_spot_id


def test_update_nonexistent_spot(client, auth_token):
    """Test updating a spot that doesn't exist."""
    fake_id = str(uuid4())
    update_payload = {"name": "Won't work"}

    response = client.put(
        f"/api/v1/skate-spots/{fake_id}",
        json=update_payload,
        cookies={"access_token": auth_token},
    )
    assert response.status_code == 404
    assert f"Skate spot with id {fake_id} not found" in response.json()["detail"]


def test_update_spot_invalid_data(client, created_spot_id, auth_token):
    """Test updating with invalid data."""
    invalid_update = {
        "name": "",  # Invalid: empty name
        "difficulty": "invalid_difficulty",  # Invalid: not in enum
    }

    response = client.put(
        f"/api/v1/skate-spots/{created_spot_id}",
        json=invalid_update,
        cookies={"access_token": auth_token},
    )
    assert response.status_code == 422  # Validation error


# Delete tests
def test_delete_spot(client, created_spot_id, auth_token):
    """Test deleting an existing spot."""
    delete_response = client.delete(
        f"/api/v1/skate-spots/{created_spot_id}",
        cookies={"access_token": auth_token},
    )
    assert delete_response.status_code == 200


def test_get_deleted_spot_returns_404(client, deleted_spot_id):
    """Test that getting a deleted spot returns 404."""
    get_response = client.get(f"/api/v1/skate-spots/{deleted_spot_id}")
    assert get_response.status_code == 404


def test_delete_nonexistent_spot(client, auth_token):
    """Test deleting a spot that doesn't exist."""
    fake_id = str(uuid4())
    response = client.delete(
        f"/api/v1/skate-spots/{fake_id}",
        cookies={"access_token": auth_token},
    )

    assert response.status_code == 404
    assert f"Skate spot with id {fake_id} not found" in response.json()["detail"]


# Form data tests
def test_create_spot_with_form_data(client, auth_token):
    """Test creating a spot with form data instead of JSON."""
    form_data = {
        "name": "Form Test Spot",
        "description": "A spot created via form submission",
        "spot_type": "park",
        "difficulty": "beginner",
        "latitude": 34.0522,
        "longitude": -118.2437,
        "city": "Los Angeles",
        "country": "USA",
        "address": "456 Form St",
        "is_public": True,
        "requires_permission": False,
    }

    response = client.post(
        "/api/v1/skate-spots/",
        data=form_data,
        cookies={"access_token": auth_token},
    )
    assert response.status_code == 201

    data = response.json()
    assert data["name"] == "Form Test Spot"
    assert data["spot_type"] == "park"
    assert data["difficulty"] == "beginner"
    assert data["location"]["city"] == "Los Angeles"


def test_update_spot_with_form_data(client, created_spot_id, auth_token):
    """Test updating a spot with form data instead of JSON."""
    form_data = {
        "name": "Updated via Form",
        "description": "Updated description",
        "spot_type": "bowl",
        "difficulty": "expert",
        "latitude": 34.0522,
        "longitude": -118.2437,
        "city": "Los Angeles",
        "country": "USA",
        "is_public": False,
        "requires_permission": True,
    }

    response = client.put(
        f"/api/v1/skate-spots/{created_spot_id}",
        data=form_data,
        cookies={"access_token": auth_token},
    )
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "Updated via Form"
    assert data["spot_type"] == "bowl"
    assert data["difficulty"] == "expert"
    assert data["is_public"] is False
    assert data["requires_permission"] is True


# GeoJSON endpoint tests
def test_get_geojson_empty(client):
    """Test GeoJSON endpoint with no spots."""
    response = client.get("/api/v1/skate-spots/geojson")
    assert response.status_code == 200

    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert data["features"] == []


def test_get_geojson_with_single_spot(client, created_spot_id):  # noqa: ARG001
    """Test GeoJSON endpoint with one spot."""
    response = client.get("/api/v1/skate-spots/geojson")
    assert response.status_code == 200

    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 1

    feature = data["features"][0]
    assert feature["type"] == "Feature"
    assert feature["geometry"]["type"] == "Point"
    assert feature["geometry"]["coordinates"] == [-74.0060, 40.7128]
    assert feature["properties"]["name"] == "API Test Spot"
    assert feature["properties"]["spot_type"] == "rail"
    assert feature["properties"]["difficulty"] == "intermediate"


def test_get_geojson_with_multiple_spots(client, sample_spot_payload, auth_token):
    """Test GeoJSON endpoint with multiple spots."""
    # Create first spot
    client.post(
        "/api/v1/skate-spots/",
        json=sample_spot_payload,
        cookies={"access_token": auth_token},
    )

    # Create second spot with different coordinates
    second_payload = sample_spot_payload.copy()
    second_payload["name"] = "Second Spot"
    second_payload["location"] = {
        "latitude": 34.0522,
        "longitude": -118.2437,
        "city": "Los Angeles",
        "country": "USA",
    }
    client.post(
        "/api/v1/skate-spots/",
        json=second_payload,
        cookies={"access_token": auth_token},
    )

    # Create third spot
    third_payload = sample_spot_payload.copy()
    third_payload["name"] = "Third Spot"
    third_payload["location"] = {
        "latitude": 51.5074,
        "longitude": -0.1278,
        "city": "London",
        "country": "UK",
    }
    client.post(
        "/api/v1/skate-spots/",
        json=third_payload,
        cookies={"access_token": auth_token},
    )

    response = client.get("/api/v1/skate-spots/geojson")
    assert response.status_code == 200

    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 3

    # Verify all features have proper structure
    for feature in data["features"]:
        assert feature["type"] == "Feature"
        assert "geometry" in feature
        assert "properties" in feature
        assert feature["geometry"]["type"] == "Point"
        assert len(feature["geometry"]["coordinates"]) == 2


def test_geojson_filters(client, sample_spot_payload, auth_token):
    """GeoJSON endpoint should honour query parameters."""

    client.post(
        "/api/v1/skate-spots/",
        json=sample_spot_payload,
        cookies={"access_token": auth_token},
    )

    restricted_payload = sample_spot_payload.copy()
    restricted_payload["name"] = "Restricted Bowl"
    restricted_payload["spot_type"] = SpotType.BOWL.value
    restricted_payload["difficulty"] = Difficulty.ADVANCED.value
    restricted_payload["is_public"] = False
    restricted_payload["requires_permission"] = True
    restricted_payload["location"] = {
        **sample_spot_payload["location"],
        "city": "Los Angeles",
    }

    client.post(
        "/api/v1/skate-spots/",
        json=restricted_payload,
        cookies={"access_token": auth_token},
    )

    response = client.get(
        "/api/v1/skate-spots/geojson",
        params={"requires_permission": "true", "is_public": "false"},
    )
    assert response.status_code == 200

    data = response.json()
    assert len(data["features"]) == 1
    assert data["features"][0]["properties"]["name"] == "Restricted Bowl"


def test_geojson_feature_properties(client, sample_spot_payload, auth_token):
    """Test that GeoJSON features include all required properties."""
    # Create a spot with all fields populated
    full_payload = sample_spot_payload.copy()
    full_payload["location"]["address"] = "456 Test Avenue"
    client.post(
        "/api/v1/skate-spots/",
        json=full_payload,
        cookies={"access_token": auth_token},
    )

    response = client.get("/api/v1/skate-spots/geojson")
    assert response.status_code == 200

    feature = response.json()["features"][0]
    props = feature["properties"]

    # Check all required properties exist
    assert "id" in props
    assert "name" in props
    assert "description" in props
    assert "spot_type" in props
    assert "difficulty" in props
    assert "city" in props
    assert "country" in props
    assert "address" in props
    assert "is_public" in props
    assert "requires_permission" in props

    # Verify values
    assert props["name"] == "API Test Spot"
    assert props["city"] == "New York"
    assert props["address"] == "456 Test Avenue"


def test_geojson_coordinates_order(client, sample_spot_payload, auth_token):
    """Test that GeoJSON coordinates are in [longitude, latitude] order."""
    # GeoJSON spec requires [longitude, latitude], not [latitude, longitude]
    payload = sample_spot_payload.copy()
    payload["location"]["latitude"] = 45.5231
    payload["location"]["longitude"] = -122.6765
    client.post(
        "/api/v1/skate-spots/",
        json=payload,
        cookies={"access_token": auth_token},
    )

    response = client.get("/api/v1/skate-spots/geojson")
    feature = response.json()["features"][0]

    coords = feature["geometry"]["coordinates"]
    assert coords[0] == -122.6765  # longitude first
    assert coords[1] == 45.5231  # latitude second
