"""API tests for user profiles."""

import pytest

from app.models.skate_spot import Difficulty, Location, SkateSpotCreate, SpotType


@pytest.fixture
def profile_spot_payload():
    """Spot payload for profile tests."""
    return SkateSpotCreate(
        name="Profile Test Spot",
        description="Spot for profile API tests",
        spot_type=SpotType.PARK,
        difficulty=Difficulty.BEGINNER,
        location=Location(
            latitude=40.7128,
            longitude=-74.0060,
            city="New York",
            country="USA",
        ),
        is_public=True,
        requires_permission=False,
    ).model_dump()


def test_get_profile_by_username(client, test_user):
    """Test fetching a user profile by username."""
    response = client.get(f"/api/v1/profiles/{test_user.username}")
    assert response.status_code == 200

    profile = response.json()
    assert profile["user"]["username"] == test_user.username
    assert "statistics" in profile
    assert "recent_spots" in profile
    assert "recent_comments" in profile
    assert "recent_ratings" in profile
    assert "activity" in profile


def test_get_nonexistent_profile(client):
    """Test fetching a profile for a non-existent user."""
    response = client.get("/api/v1/profiles/nonexistent_user_12345")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_profile_statistics(client, auth_token, profile_spot_payload):
    """Test that profile statistics are correctly calculated."""
    # Create a spot
    spot_response = client.post(
        "/api/v1/skate-spots/",
        json=profile_spot_payload,
        cookies={"access_token": auth_token},
    )
    assert spot_response.status_code == 201

    # Get the profile
    response = client.get("/api/v1/profiles/testuser")
    assert response.status_code == 200

    profile = response.json()
    assert profile["statistics"]["spots_added"] >= 1


def test_profile_recent_spots(client, auth_token, profile_spot_payload):
    """Test that recent spots are included in the profile."""
    # Create a spot
    spot_response = client.post(
        "/api/v1/skate-spots/",
        json=profile_spot_payload,
        cookies={"access_token": auth_token},
    )
    assert spot_response.status_code == 201

    # Get the profile
    response = client.get("/api/v1/profiles/testuser")
    assert response.status_code == 200

    profile = response.json()
    assert len(profile["recent_spots"]) >= 1
    assert profile["recent_spots"][0]["name"] == profile_spot_payload["name"]


def test_public_profile_page(client, test_user):
    """Test that public profile HTML page is accessible."""
    response = client.get(f"/users/{test_user.username}")
    assert response.status_code == 200
    assert test_user.username in response.text


def test_public_profile_page_not_found(client):
    """Test that non-existent profile page returns 404."""
    response = client.get("/users/nonexistent_user_12345")
    assert response.status_code == 404
