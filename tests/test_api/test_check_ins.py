"""API tests for spot check-in endpoints."""

from __future__ import annotations

from app.models.skate_spot import Difficulty, SpotType


def _create_spot(client, auth_token):
    payload = {
        "name": "Check-In Spot",
        "description": "Perfect ledges for nose slides.",
        "spot_type": SpotType.STREET.value,
        "difficulty": Difficulty.BEGINNER.value,
        "location": {
            "latitude": 37.7749,
            "longitude": -122.4194,
            "address": "Market St",
            "city": "San Francisco",
            "country": "USA",
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


def test_check_in_lifecycle(client, auth_token):
    spot_id = _create_spot(client, auth_token)

    create_response = client.post(
        f"/api/v1/skate-spots/{spot_id}/check-ins",
        json={"status": "arrived", "message": "Session is live!"},
        cookies={"access_token": auth_token},
    )
    assert create_response.status_code == 200
    created = create_response.json()
    assert created["status"] == "arrived"
    assert created["message"] == "Session is live!"
    check_in_id = created["id"]

    list_response = client.get(f"/api/v1/skate-spots/{spot_id}/check-ins")
    assert list_response.status_code == 200
    listed = list_response.json()
    assert len(listed) == 1
    assert listed[0]["id"] == check_in_id

    checkout_response = client.post(
        f"/api/v1/check-ins/{check_in_id}/checkout",
        json={"message": "Peace out"},
        cookies={"access_token": auth_token},
    )
    assert checkout_response.status_code == 200
    ended = checkout_response.json()
    assert ended["is_active"] is False
    assert ended["ended_at"] is not None


def test_check_in_requires_authentication(client):
    fake_spot_id = "00000000-0000-0000-0000-000000000000"
    response = client.post(
        f"/api/v1/skate-spots/{fake_spot_id}/check-ins",
        json={"status": "arrived"},
    )
    assert response.status_code == 401


def test_list_check_ins_missing_spot_returns_404(client):
    response = client.get("/api/v1/skate-spots/00000000-0000-0000-0000-000000000000/check-ins")
    assert response.status_code == 404
