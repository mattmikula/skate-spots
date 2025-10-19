"""API tests for skate spot comments."""

from uuid import uuid4

import pytest

from app.core.security import create_access_token, get_password_hash
from app.models.skate_spot import Difficulty, SpotType
from app.models.user import UserCreate
from app.repositories.user_repository import UserRepository


@pytest.fixture
def created_spot_id(client, auth_token):
    """Create a skate spot and return its ID for comment tests."""

    payload = {
        "name": "Comment API Spot",
        "description": "Spot created for comment API tests",
        "spot_type": SpotType.PARK.value,
        "difficulty": Difficulty.INTERMEDIATE.value,
        "location": {
            "latitude": 51.5074,
            "longitude": -0.1278,
            "address": "10 Downing St",
            "city": "London",
            "country": "UK",
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


@pytest.fixture
def other_token(session_factory):
    """Authentication token for a secondary user."""

    db = session_factory()
    try:
        repo = UserRepository(db)
        user_data = UserCreate(
            email="other-comment@example.com",
            username="othercommenter",
            password="commentpass123",
        )
        hashed = get_password_hash("commentpass123")
        user = repo.create(user_data, hashed)
        token = create_access_token(data={"sub": str(user.id), "username": user.username})
        return token
    finally:
        db.close()


def test_comment_lifecycle(client, auth_token, created_spot_id):
    """Users can create, list, and delete comments through the API."""

    create_response = client.post(
        f"/api/v1/skate-spots/{created_spot_id}/comments/",
        json={"content": "Amazing flatground area."},
        cookies={"access_token": auth_token},
    )
    assert create_response.status_code == 201
    comments = create_response.json()
    assert len(comments) == 1
    assert comments[0]["content"] == "Amazing flatground area."
    assert comments[0]["author"]["username"] == "testuser"

    list_response = client.get(f"/api/v1/skate-spots/{created_spot_id}/comments/")
    assert list_response.status_code == 200
    listed = list_response.json()
    assert len(listed) == 1
    comment_id = listed[0]["id"]

    delete_response = client.delete(
        f"/api/v1/skate-spots/{created_spot_id}/comments/{comment_id}",
        cookies={"access_token": auth_token},
    )
    assert delete_response.status_code == 204

    after_delete = client.get(f"/api/v1/skate-spots/{created_spot_id}/comments/")
    assert after_delete.status_code == 200
    assert after_delete.json() == []


def test_comment_delete_requires_permission(client, auth_token, other_token, created_spot_id):
    """Only owners or admins can delete comments."""

    create_response = client.post(
        f"/api/v1/skate-spots/{created_spot_id}/comments/",
        json={"content": "Original author."},
        cookies={"access_token": auth_token},
    )
    comment_id = create_response.json()[0]["id"]

    forbidden_response = client.delete(
        f"/api/v1/skate-spots/{created_spot_id}/comments/{comment_id}",
        cookies={"access_token": other_token},
    )
    assert forbidden_response.status_code == 403

    owner_delete = client.delete(
        f"/api/v1/skate-spots/{created_spot_id}/comments/{comment_id}",
        cookies={"access_token": auth_token},
    )
    assert owner_delete.status_code == 204


def test_comment_endpoints_validate_spot(client, auth_token):
    """Comment endpoints return 404 when the spot does not exist."""

    fake_spot_id = str(uuid4())

    list_response = client.get(f"/api/v1/skate-spots/{fake_spot_id}/comments/")
    assert list_response.status_code == 404

    create_response = client.post(
        f"/api/v1/skate-spots/{fake_spot_id}/comments/",
        json={"content": "Will not work"},
        cookies={"access_token": auth_token},
    )
    assert create_response.status_code == 404

    delete_response = client.delete(
        f"/api/v1/skate-spots/{fake_spot_id}/comments/{fake_spot_id}",
        cookies={"access_token": auth_token},
    )
    assert delete_response.status_code == 404
