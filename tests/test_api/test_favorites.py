"""API tests for favourite skate spots."""

import pytest

from app.models.skate_spot import Difficulty, Location, SkateSpotCreate, SpotType


@pytest.fixture
def favorite_spot_payload():
    return SkateSpotCreate(
        name="API Favourite Spot",
        description="Spot for favourites API tests",
        spot_type=SpotType.RAIL,
        difficulty=Difficulty.INTERMEDIATE,
        location=Location(
            latitude=48.8566,
            longitude=2.3522,
            city="Paris",
            country="France",
        ),
        is_public=True,
        requires_permission=False,
    ).model_dump()


def create_spot_via_api(client, payload, auth_token):
    response = client.post(
        "/api/v1/skate-spots/",
        json=payload,
        cookies={"access_token": auth_token},
    )
    response.raise_for_status()
    return response.json()["id"]


def test_list_favorites_starts_empty(client, auth_token):
    response = client.get("/api/v1/users/me/favorites/", cookies={"access_token": auth_token})
    assert response.status_code == 200
    assert response.json() == []


def test_add_and_remove_favorite(client, auth_token, favorite_spot_payload):
    spot_id = create_spot_via_api(client, favorite_spot_payload, auth_token)

    add_response = client.put(
        f"/api/v1/users/me/favorites/{spot_id}",
        cookies={"access_token": auth_token},
    )
    assert add_response.status_code == 200
    assert add_response.json()["is_favorite"] is True

    list_response = client.get("/api/v1/users/me/favorites/", cookies={"access_token": auth_token})
    assert list_response.status_code == 200
    favorites = list_response.json()
    assert len(favorites) == 1
    assert favorites[0]["id"] == spot_id

    remove_response = client.delete(
        f"/api/v1/users/me/favorites/{spot_id}",
        cookies={"access_token": auth_token},
    )
    assert remove_response.status_code == 200
    assert remove_response.json()["is_favorite"] is False

    list_after = client.get("/api/v1/users/me/favorites/", cookies={"access_token": auth_token})
    assert list_after.status_code == 200
    assert list_after.json() == []


def test_toggle_favorite_endpoint(client, auth_token, favorite_spot_payload):
    spot_id = create_spot_via_api(client, favorite_spot_payload, auth_token)

    first = client.post(
        f"/api/v1/users/me/favorites/{spot_id}/toggle",
        cookies={"access_token": auth_token},
    )
    assert first.status_code == 200
    assert first.json()["is_favorite"] is True

    second = client.post(
        f"/api/v1/users/me/favorites/{spot_id}/toggle",
        cookies={"access_token": auth_token},
    )
    assert second.status_code == 200
    assert second.json()["is_favorite"] is False


def test_favorite_requires_authentication(client, favorite_spot_payload, auth_token):
    spot_id = create_spot_via_api(client, favorite_spot_payload, auth_token)

    response = client.put(f"/api/v1/users/me/favorites/{spot_id}")
    assert response.status_code == 401
