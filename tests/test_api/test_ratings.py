"""Tests for the ratings API endpoints."""

import pytest
from uuid import uuid4

from app.models.rating import RatingCreate
from app.models.skate_spot import Difficulty, Location, SpotType, SkateSpotCreate
from app.services.rating_service import RatingService, get_rating_service
from app.repositories.rating_repository import RatingRepository


@pytest.fixture
def app_with_ratings(client, session_factory):
    """Update client to include rating service dependencies."""
    from main import app

    def get_rating_service_override():
        return RatingService(RatingRepository(session_factory=session_factory))

    app.dependency_overrides[get_rating_service] = get_rating_service_override

    yield client

    app.dependency_overrides.pop(get_rating_service, None)


@pytest.fixture
def test_spot_with_owner(client, app_with_ratings, auth_token):
    """Create a test spot for rating tests."""
    response = client.post(
        "/api/v1/skate-spots/",
        json={
            "name": "Rating Test Spot",
            "description": "A spot for testing ratings",
            "spot_type": "park",
            "difficulty": "beginner",
            "location": {
                "latitude": 40.7128,
                "longitude": -74.0060,
                "city": "New York",
                "country": "USA",
            },
        },
        cookies={"access_token": auth_token},
    )
    assert response.status_code == 201
    return response.json()


def test_create_rating(app_with_ratings, test_spot_with_owner, auth_token):
    """Test creating a rating through API."""
    spot_id = test_spot_with_owner["id"]

    response = app_with_ratings.post(
        f"/api/v1/skate-spots/{spot_id}/ratings/",
        json={"score": 5, "review": "Amazing spot!"},
        cookies={"access_token": auth_token},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["score"] == 5
    assert data["review"] == "Amazing spot!"
    assert data["spot_id"] == spot_id


def test_create_rating_invalid_score(app_with_ratings, test_spot_with_owner, auth_token):
    """Test creating a rating with invalid score."""
    spot_id = test_spot_with_owner["id"]

    response = app_with_ratings.post(
        f"/api/v1/skate-spots/{spot_id}/ratings/",
        json={"score": 10, "review": "Invalid score"},
        cookies={"access_token": auth_token},
    )

    assert response.status_code == 422


def test_create_rating_unauthorized(app_with_ratings, test_spot_with_owner):
    """Test creating a rating without authentication."""
    spot_id = test_spot_with_owner["id"]

    response = app_with_ratings.post(
        f"/api/v1/skate-spots/{spot_id}/ratings/",
        json={"score": 5, "review": "Test"},
    )

    assert response.status_code == 401


def test_create_duplicate_rating(app_with_ratings, test_spot_with_owner, auth_token):
    """Test that a user can only rate a spot once."""
    spot_id = test_spot_with_owner["id"]

    # Create first rating
    response1 = app_with_ratings.post(
        f"/api/v1/skate-spots/{spot_id}/ratings/",
        json={"score": 5},
        cookies={"access_token": auth_token},
    )
    assert response1.status_code == 201

    # Try to create second rating
    response2 = app_with_ratings.post(
        f"/api/v1/skate-spots/{spot_id}/ratings/",
        json={"score": 4},
        cookies={"access_token": auth_token},
    )
    assert response2.status_code == 409


def test_list_ratings(app_with_ratings, test_spot_with_owner, auth_token, client):
    """Test listing all ratings for a spot."""
    spot_id = test_spot_with_owner["id"]

    # Create a rating
    create_response = app_with_ratings.post(
        f"/api/v1/skate-spots/{spot_id}/ratings/",
        json={"score": 5, "review": "Excellent!"},
        cookies={"access_token": auth_token},
    )
    assert create_response.status_code == 201

    # List ratings
    list_response = app_with_ratings.get(
        f"/api/v1/skate-spots/{spot_id}/ratings/"
    )
    assert list_response.status_code == 200
    data = list_response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_list_ratings_nonexistent_spot(app_with_ratings):
    """Test listing ratings for a non-existent spot."""
    spot_id = str(uuid4())

    response = app_with_ratings.get(
        f"/api/v1/skate-spots/{spot_id}/ratings/"
    )
    assert response.status_code == 404


def test_get_rating_stats(app_with_ratings, test_spot_with_owner, auth_token, client):
    """Test getting rating statistics."""
    spot_id = test_spot_with_owner["id"]

    # Create a rating
    app_with_ratings.post(
        f"/api/v1/skate-spots/{spot_id}/ratings/",
        json={"score": 4, "review": "Good"},
        cookies={"access_token": auth_token},
    )

    # Get stats
    response = app_with_ratings.get(
        f"/api/v1/skate-spots/{spot_id}/ratings/stats"
    )
    assert response.status_code == 200
    data = response.json()
    assert "average_score" in data
    assert "total_ratings" in data
    assert data["total_ratings"] >= 1


def test_get_rating_stats_empty_spot(app_with_ratings, test_spot_with_owner):
    """Test getting stats for a spot with no ratings."""
    spot_id = test_spot_with_owner["id"]

    response = app_with_ratings.get(
        f"/api/v1/skate-spots/{spot_id}/ratings/stats"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["average_score"] == 0
    assert data["total_ratings"] == 0


def test_get_single_rating(app_with_ratings, test_spot_with_owner, auth_token):
    """Test getting a single rating by ID."""
    spot_id = test_spot_with_owner["id"]

    # Create a rating
    create_response = app_with_ratings.post(
        f"/api/v1/skate-spots/{spot_id}/ratings/",
        json={"score": 5, "review": "Perfect!"},
        cookies={"access_token": auth_token},
    )
    rating_id = create_response.json()["id"]

    # Get the rating
    response = app_with_ratings.get(
        f"/api/v1/skate-spots/{spot_id}/ratings/{rating_id}"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == rating_id
    assert data["score"] == 5


def test_get_rating_from_wrong_spot(app_with_ratings, test_spot_with_owner, auth_token, client):
    """Test getting a rating from a wrong spot ID."""
    spot_id = test_spot_with_owner["id"]

    # Create a rating
    create_response = app_with_ratings.post(
        f"/api/v1/skate-spots/{spot_id}/ratings/",
        json={"score": 5},
        cookies={"access_token": auth_token},
    )
    rating_id = create_response.json()["id"]

    # Try to get rating from different spot
    wrong_spot_id = str(uuid4())
    response = app_with_ratings.get(
        f"/api/v1/skate-spots/{wrong_spot_id}/ratings/{rating_id}"
    )
    assert response.status_code == 404


def test_update_rating(app_with_ratings, test_spot_with_owner, auth_token):
    """Test updating a rating."""
    spot_id = test_spot_with_owner["id"]

    # Create a rating
    create_response = app_with_ratings.post(
        f"/api/v1/skate-spots/{spot_id}/ratings/",
        json={"score": 2, "review": "Not great"},
        cookies={"access_token": auth_token},
    )
    rating_id = create_response.json()["id"]

    # Update the rating
    update_response = app_with_ratings.put(
        f"/api/v1/skate-spots/{spot_id}/ratings/{rating_id}",
        json={"score": 5, "review": "Actually amazing!"},
        cookies={"access_token": auth_token},
    )
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["score"] == 5
    assert data["review"] == "Actually amazing!"


def test_update_rating_unauthorized(app_with_ratings, test_spot_with_owner, auth_token, session_factory):
    """Test that only the owner can update a rating."""
    spot_id = test_spot_with_owner["id"]

    # Create a rating
    create_response = app_with_ratings.post(
        f"/api/v1/skate-spots/{spot_id}/ratings/",
        json={"score": 3},
        cookies={"access_token": auth_token},
    )
    rating_id = create_response.json()["id"]

    # Create another user and try to update
    from app.repositories.user_repository import UserRepository
    from app.models.user import UserCreate
    from app.core.security import get_password_hash, create_access_token

    db = session_factory()
    try:
        repo = UserRepository(db)
        user_data = UserCreate(
            email="updatetest@example.com",
            username="updatetest",
            password="password123",
        )
        hashed_password = get_password_hash("password123")
        other_user = repo.create(user_data, hashed_password)
        db.expunge(other_user)
        other_token = create_access_token(data={"sub": str(other_user.id), "username": other_user.username})
    finally:
        db.close()

    # Try to update as different user
    update_response = app_with_ratings.put(
        f"/api/v1/skate-spots/{spot_id}/ratings/{rating_id}",
        json={"score": 5},
        cookies={"access_token": other_token},
    )
    assert update_response.status_code == 403


def test_delete_rating(app_with_ratings, test_spot_with_owner, auth_token):
    """Test deleting a rating."""
    spot_id = test_spot_with_owner["id"]

    # Create a rating
    create_response = app_with_ratings.post(
        f"/api/v1/skate-spots/{spot_id}/ratings/",
        json={"score": 1, "review": "Terrible"},
        cookies={"access_token": auth_token},
    )
    rating_id = create_response.json()["id"]

    # Delete the rating
    delete_response = app_with_ratings.delete(
        f"/api/v1/skate-spots/{spot_id}/ratings/{rating_id}",
        cookies={"access_token": auth_token},
    )
    assert delete_response.status_code == 204

    # Verify it's deleted
    get_response = app_with_ratings.get(
        f"/api/v1/skate-spots/{spot_id}/ratings/{rating_id}"
    )
    assert get_response.status_code == 404


def test_delete_rating_unauthorized(app_with_ratings, test_spot_with_owner, auth_token, session_factory):
    """Test that only the owner can delete a rating."""
    spot_id = test_spot_with_owner["id"]

    # Create a rating
    create_response = app_with_ratings.post(
        f"/api/v1/skate-spots/{spot_id}/ratings/",
        json={"score": 5},
        cookies={"access_token": auth_token},
    )
    rating_id = create_response.json()["id"]

    # Create another user and try to delete
    from app.repositories.user_repository import UserRepository
    from app.models.user import UserCreate
    from app.core.security import get_password_hash, create_access_token

    db = session_factory()
    try:
        repo = UserRepository(db)
        user_data = UserCreate(
            email="deletetest@example.com",
            username="deletetest",
            password="password123",
        )
        hashed_password = get_password_hash("password123")
        other_user = repo.create(user_data, hashed_password)
        db.expunge(other_user)
        other_token = create_access_token(data={"sub": str(other_user.id), "username": other_user.username})
    finally:
        db.close()

    # Try to delete as different user
    delete_response = app_with_ratings.delete(
        f"/api/v1/skate-spots/{spot_id}/ratings/{rating_id}",
        cookies={"access_token": other_token},
    )
    assert delete_response.status_code == 403
