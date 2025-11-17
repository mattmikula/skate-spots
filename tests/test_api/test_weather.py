"""API tests for skate spot weather endpoints."""

from __future__ import annotations


def test_gets_weather_for_spot(client, auth_token):
    """Weather endpoint returns normalized data."""

    payload = {
        "name": "Weather API Spot",
        "description": "A spot to test weather output",
        "spot_type": "street",
        "difficulty": "beginner",
        "location": {
            "latitude": 37.0,
            "longitude": -122.0,
            "address": "123 Test St",
            "city": "San Jose",
            "country": "USA",
        },
        "is_public": True,
        "requires_permission": False,
    }
    create_response = client.post(
        "/api/v1/skate-spots/",
        json=payload,
        cookies={"access_token": auth_token},
    )
    spot_id = create_response.json()["id"]

    response = client.get(f"/api/v1/skate-spots/{spot_id}/weather")

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["current"]["summary"]
    assert body["cached"] is False
    assert body["data"]["forecast"]


def test_weather_endpoint_returns_503_when_provider_down(client, auth_token):
    """When provider fails and no cache exists, the API surfaces 503."""

    payload = {
        "name": "Outage Spot",
        "description": "Provider outage path",
        "spot_type": "park",
        "difficulty": "beginner",
        "location": {
            "latitude": 35.0,
            "longitude": -118.0,
            "address": "789 Test Dr",
            "city": "Los Angeles",
            "country": "USA",
        },
        "is_public": True,
        "requires_permission": False,
    }
    create_response = client.post(
        "/api/v1/skate-spots/",
        json=payload,
        cookies={"access_token": auth_token},
    )
    spot_id = create_response.json()["id"]

    client.weather_stub_client.should_fail = True  # type: ignore[attr-defined]
    response = client.get(f"/api/v1/skate-spots/{spot_id}/weather")

    assert response.status_code == 503
