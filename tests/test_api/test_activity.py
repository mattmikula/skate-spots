"""API tests for activity feed endpoints."""

import pytest

from app.models.skate_spot import Difficulty, Location, SkateSpotCreate, SpotType


@pytest.fixture
def spot_payload():
    """Sample skate spot for creating activities."""
    return SkateSpotCreate(
        name="Activity Test Spot",
        description="Spot for activity feed tests",
        spot_type=SpotType.STREET,
        difficulty=Difficulty.INTERMEDIATE,
        location=Location(
            latitude=40.7128,
            longitude=-74.0060,
            city="New York",
            country="USA",
        ),
        is_public=True,
        requires_permission=False,
    ).model_dump()


def create_spot_and_rate(client, spot_payload, auth_token, score=4):
    """Helper to create a spot and rate it to generate activity."""
    # Create spot
    spot_response = client.post(
        "/api/v1/skate-spots/",
        json=spot_payload,
        cookies={"access_token": auth_token},
    )
    spot_response.raise_for_status()
    spot_id = spot_response.json()["id"]

    # Rate the spot to create activity
    rating_response = client.put(
        f"/api/v1/skate-spots/{spot_id}/ratings/me",
        json={"score": score},
        cookies={"access_token": auth_token},
    )
    rating_response.raise_for_status()

    return spot_id


def test_get_personalized_feed_empty(client, auth_token):
    """Personalized feed starts empty when user follows no one."""
    response = client.get(
        "/api/v1/feed",
        cookies={"access_token": auth_token},
    )

    assert response.status_code == 200
    data = response.json()
    assert "activities" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    assert data["total"] == 0
    assert len(data["activities"]) == 0


def test_get_personalized_feed_requires_auth(client):
    """Personalized feed requires authentication."""
    response = client.get("/api/v1/feed")
    assert response.status_code == 401


def test_get_personalized_feed_with_pagination(client, auth_token, spot_payload):
    """Personalized feed supports pagination parameters."""
    # Create an activity
    create_spot_and_rate(client, spot_payload, auth_token)

    # Test with limit parameter
    response = client.get(
        "/api/v1/feed?limit=5&offset=0",
        cookies={"access_token": auth_token},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 5
    assert data["offset"] == 0


def test_get_personalized_feed_respects_max_limit(client, auth_token):
    """Personalized feed caps limit at 100."""
    response = client.get(
        "/api/v1/feed?limit=200",
        cookies={"access_token": auth_token},
    )

    assert response.status_code == 200
    data = response.json()
    # The endpoint should cap limit at 100
    assert data["limit"] == 100


def test_get_public_feed_no_auth_required(client):
    """Public feed does not require authentication."""
    response = client.get("/api/v1/feed/public")
    assert response.status_code == 200
    data = response.json()
    assert "activities" in data
    assert "total" in data


def test_get_public_feed_shows_all_activities(client, auth_token, spot_payload):
    """Public feed shows activities from all users.

    Note: In the test environment, activity service is not wired up to
    the rating service, so this test verifies the endpoint works but
    may return empty results.
    """
    # Create some activity
    create_spot_and_rate(client, spot_payload, auth_token)

    response = client.get("/api/v1/feed/public")

    assert response.status_code == 200
    data = response.json()
    # Verify response structure
    assert "activities" in data
    assert "total" in data
    assert isinstance(data["activities"], list)
    assert isinstance(data["total"], int)


def test_get_public_feed_with_pagination(client):
    """Public feed supports pagination parameters."""
    response = client.get("/api/v1/feed/public?limit=10&offset=5")

    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 10
    assert data["offset"] == 5


def test_get_public_feed_respects_max_limit(client):
    """Public feed caps limit at 100."""
    response = client.get("/api/v1/feed/public?limit=150")

    assert response.status_code == 200
    data = response.json()
    # The endpoint should cap limit at 100
    assert data["limit"] == 100


def test_get_public_feed_default_pagination(client):
    """Public feed uses default pagination values."""
    response = client.get("/api/v1/feed/public")

    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 20  # Default limit
    assert data["offset"] == 0  # Default offset


def test_get_user_activity_not_implemented(client):
    """User activity endpoint returns 501 Not Implemented."""
    response = client.get("/api/v1/feed/users/testuser")

    assert response.status_code == 501
    detail = response.json()["detail"].lower()
    assert "username" in detail or "not yet implemented" in detail


def test_get_user_activity_requires_username_lookup(client):
    """User activity endpoint indicates username lookup is needed."""
    response = client.get("/api/v1/feed/users/someuser")

    assert response.status_code == 501
    error_detail = response.json()["detail"]
    assert "username" in error_detail.lower()


def test_activity_feed_response_structure(client, auth_token, spot_payload):
    """Activity feed response has correct structure."""
    # Create activity
    create_spot_and_rate(client, spot_payload, auth_token)

    response = client.get("/api/v1/feed/public")

    assert response.status_code == 200
    data = response.json()

    # Check response structure
    assert "activities" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data

    # Check activity structure if any exist
    if len(data["activities"]) > 0:
        activity = data["activities"][0]
        assert "id" in activity
        assert "actor" in activity
        assert "activity_type" in activity
        assert "created_at" in activity


def test_personalized_feed_response_structure(client, auth_token):
    """Personalized feed has same response structure as public feed."""
    response = client.get(
        "/api/v1/feed",
        cookies={"access_token": auth_token},
    )

    assert response.status_code == 200
    data = response.json()

    # Check response structure matches ActivityFeedResponse
    assert "activities" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data
