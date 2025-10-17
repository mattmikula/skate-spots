"""API tests for skate spot ratings."""

from uuid import uuid4

import pytest

from app.models.skate_spot import Difficulty, SpotType


@pytest.fixture
def rating_payload():
    """Return a valid payload for creating or updating a rating."""

    return {
        "score": 4,
        "comment": "Smooth surface and great rails.",
    }


@pytest.fixture
def created_spot_id(client, auth_token):
    """Create a new skate spot for rating tests and return its ID."""

    payload = {
        "name": "Rating API Spot",
        "description": "Spot created for rating API tests",
        "spot_type": SpotType.PARK.value,
        "difficulty": Difficulty.INTERMEDIATE.value,
        "location": {
            "latitude": 35.6895,
            "longitude": 139.6917,
            "address": "1 Chiyoda",
            "city": "Tokyo",
            "country": "Japan",
        },
        "is_public": True,
        "requires_permission": False,
    }
    response = client.post(
        "/api/v1/skate-spots/",
        json=payload,
        cookies={"access_token": auth_token},
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_rating_lifecycle(client, auth_token, created_spot_id, rating_payload):
    """Users can create, update, retrieve, and delete their ratings."""

    # Create rating
    put_response = client.put(
        f"/api/v1/skate-spots/{created_spot_id}/ratings/me",
        json=rating_payload,
        cookies={"access_token": auth_token},
    )
    assert put_response.status_code == 200
    summary = put_response.json()
    assert summary["ratings_count"] == 1
    assert summary["average_score"] == 4.0
    assert summary["user_rating"]["score"] == 4
    assert summary["user_rating"]["comment"] == "Smooth surface and great rails."

    # Fetch summary anonymously (no user rating)
    anon_summary_response = client.get(
        f"/api/v1/skate-spots/{created_spot_id}/ratings/summary",
    )
    assert anon_summary_response.status_code == 200
    anon_summary = anon_summary_response.json()
    assert anon_summary["average_score"] == 4.0
    assert anon_summary["ratings_count"] == 1
    assert anon_summary["user_rating"] is None

    # Fetch summary as authenticated user (includes personal rating)
    authed_summary_response = client.get(
        f"/api/v1/skate-spots/{created_spot_id}/ratings/summary",
        cookies={"access_token": auth_token},
    )
    assert authed_summary_response.status_code == 200
    authed_summary = authed_summary_response.json()
    assert authed_summary["user_rating"]["score"] == 4

    # Fetch individual rating
    get_response = client.get(
        f"/api/v1/skate-spots/{created_spot_id}/ratings/me",
        cookies={"access_token": auth_token},
    )
    assert get_response.status_code == 200
    rating = get_response.json()
    assert rating["score"] == 4

    # Update rating
    updated_payload = {"score": 5, "comment": "Even better after the update."}
    update_response = client.put(
        f"/api/v1/skate-spots/{created_spot_id}/ratings/me",
        json=updated_payload,
        cookies={"access_token": auth_token},
    )
    assert update_response.status_code == 200
    updated_summary = update_response.json()
    assert updated_summary["average_score"] == 5.0
    assert updated_summary["ratings_count"] == 1
    assert updated_summary["user_rating"]["score"] == 5

    spot_response = client.get(f"/api/v1/skate-spots/{created_spot_id}")
    assert spot_response.status_code == 200
    spot_data = spot_response.json()
    assert spot_data["average_rating"] == 5.0
    assert spot_data["ratings_count"] == 1

    # Delete rating
    delete_response = client.delete(
        f"/api/v1/skate-spots/{created_spot_id}/ratings/me",
        cookies={"access_token": auth_token},
    )
    assert delete_response.status_code == 200
    deleted_summary = delete_response.json()
    assert deleted_summary["ratings_count"] == 0
    assert deleted_summary["average_score"] is None
    assert deleted_summary["user_rating"] is None

    spot_after_delete = client.get(f"/api/v1/skate-spots/{created_spot_id}")
    assert spot_after_delete.status_code == 200
    spot_after_delete_data = spot_after_delete.json()
    assert spot_after_delete_data["average_rating"] is None
    assert spot_after_delete_data["ratings_count"] == 0

    # Fetch rating after deletion returns 404
    missing_response = client.get(
        f"/api/v1/skate-spots/{created_spot_id}/ratings/me",
        cookies={"access_token": auth_token},
    )
    assert missing_response.status_code == 404


def test_rating_endpoints_validate_spot(client, auth_token):
    """Rating endpoints return 404 when the spot does not exist."""

    fake_spot_id = str(uuid4())

    summary_response = client.get(f"/api/v1/skate-spots/{fake_spot_id}/ratings/summary")
    assert summary_response.status_code == 404

    put_response = client.put(
        f"/api/v1/skate-spots/{fake_spot_id}/ratings/me",
        json={"score": 3},
        cookies={"access_token": auth_token},
    )
    assert put_response.status_code == 404

    delete_response = client.delete(
        f"/api/v1/skate-spots/{fake_spot_id}/ratings/me",
        cookies={"access_token": auth_token},
    )
    assert delete_response.status_code == 404
