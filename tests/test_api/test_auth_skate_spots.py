"""Tests for authentication and authorization on skate spot endpoints."""

import pytest


@pytest.fixture
def sample_spot_data():
    """Sample skate spot data for testing."""
    return {
        "name": "Test Skate Park",
        "description": "A great place to skate",
        "spot_type": "skatepark",
        "difficulty": "intermediate",
        "location": {
            "latitude": 37.7749,
            "longitude": -122.4194,
            "city": "San Francisco",
            "country": "USA",
            "address": "123 Main St",
        },
        "is_public": True,
        "requires_permission": False,
    }


class TestCreateSpotAuthentication:
    """Tests for authentication on creating skate spots."""

    def test_create_spot_authenticated(self, client, test_user, auth_token, sample_spot_data):
        """Test that authenticated users can create spots."""
        response = client.post(
            "/api/v1/skate-spots/",
            json=sample_spot_data,
            cookies={"access_token": auth_token},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Skate Park"
        assert "id" in data

    def test_create_spot_unauthenticated(self, client, sample_spot_data):
        """Test that unauthenticated users cannot create spots."""
        response = client.post(
            "/api/v1/skate-spots/",
            json=sample_spot_data,
        )

        assert response.status_code == 401

    def test_create_spot_invalid_token(self, client, sample_spot_data):
        """Test that invalid token is rejected."""
        response = client.post(
            "/api/v1/skate-spots/",
            json=sample_spot_data,
            cookies={"access_token": "invalid-token"},
        )

        assert response.status_code == 401


class TestUpdateSpotAuthorization:
    """Tests for authorization on updating skate spots."""

    def test_update_own_spot(self, client, test_user, auth_token, sample_spot_data):
        """Test that users can update their own spots."""
        # Create a spot
        create_response = client.post(
            "/api/v1/skate-spots/",
            json=sample_spot_data,
            cookies={"access_token": auth_token},
        )
        spot_id = create_response.json()["id"]

        # Update the spot
        update_data = sample_spot_data.copy()
        update_data["name"] = "Updated Skate Park"

        update_response = client.put(
            f"/api/v1/skate-spots/{spot_id}",
            json=update_data,
            cookies={"access_token": auth_token},
        )

        assert update_response.status_code == 200
        assert update_response.json()["name"] == "Updated Skate Park"

    def test_update_others_spot_forbidden(
        self, client, session_factory, test_user, auth_token, sample_spot_data
    ):
        """Test that users cannot update spots owned by others."""
        # Create another user and their spot
        from app.core.security import create_access_token, get_password_hash
        from app.models.user import UserCreate
        from app.repositories.user_repository import UserRepository

        db = session_factory()
        repo = UserRepository(db)
        other_user_data = UserCreate(
            email="other@example.com",
            username="otheruser",
            password="password123",
        )
        other_user = repo.create(other_user_data, get_password_hash("password123"))
        other_token = create_access_token(
            data={"sub": str(other_user.id), "username": other_user.username}
        )

        # Create spot as other user
        create_response = client.post(
            "/api/v1/skate-spots/",
            json=sample_spot_data,
            cookies={"access_token": other_token},
        )
        spot_id = create_response.json()["id"]

        # Try to update as test_user
        update_data = sample_spot_data.copy()
        update_data["name"] = "Hacked Name"

        update_response = client.put(
            f"/api/v1/skate-spots/{spot_id}",
            json=update_data,
            cookies={"access_token": auth_token},
        )

        assert update_response.status_code == 403

    def test_admin_can_update_any_spot(
        self, client, session_factory, test_user, auth_token, admin_token, sample_spot_data
    ):
        """Test that admins can update any spot."""
        # Create spot as regular user
        create_response = client.post(
            "/api/v1/skate-spots/",
            json=sample_spot_data,
            cookies={"access_token": auth_token},
        )
        spot_id = create_response.json()["id"]

        # Update as admin
        update_data = sample_spot_data.copy()
        update_data["name"] = "Admin Updated"

        update_response = client.put(
            f"/api/v1/skate-spots/{spot_id}",
            json=update_data,
            cookies={"access_token": admin_token},
        )

        assert update_response.status_code == 200
        assert update_response.json()["name"] == "Admin Updated"

    def test_update_spot_unauthenticated(self, client, test_user, auth_token, sample_spot_data):
        """Test that unauthenticated users cannot update spots."""
        # Create a spot
        create_response = client.post(
            "/api/v1/skate-spots/",
            json=sample_spot_data,
            cookies={"access_token": auth_token},
        )
        spot_id = create_response.json()["id"]

        # Try to update without authentication
        update_data = sample_spot_data.copy()
        update_data["name"] = "Hacked Name"

        update_response = client.put(
            f"/api/v1/skate-spots/{spot_id}",
            json=update_data,
        )

        assert update_response.status_code == 401


class TestDeleteSpotAuthorization:
    """Tests for authorization on deleting skate spots."""

    def test_delete_own_spot(self, client, test_user, auth_token, sample_spot_data):
        """Test that users can delete their own spots."""
        # Create a spot
        create_response = client.post(
            "/api/v1/skate-spots/",
            json=sample_spot_data,
            cookies={"access_token": auth_token},
        )
        spot_id = create_response.json()["id"]

        # Delete the spot
        delete_response = client.delete(
            f"/api/v1/skate-spots/{spot_id}",
            cookies={"access_token": auth_token},
        )

        assert delete_response.status_code == 200

        # Verify it's gone
        get_response = client.get(f"/api/v1/skate-spots/{spot_id}")
        assert get_response.status_code == 404

    def test_delete_others_spot_forbidden(
        self, client, session_factory, test_user, auth_token, sample_spot_data
    ):
        """Test that users cannot delete spots owned by others."""
        # Create another user and their spot
        from app.core.security import create_access_token, get_password_hash
        from app.models.user import UserCreate
        from app.repositories.user_repository import UserRepository

        db = session_factory()
        repo = UserRepository(db)
        other_user_data = UserCreate(
            email="other@example.com",
            username="otheruser",
            password="password123",
        )
        other_user = repo.create(other_user_data, get_password_hash("password123"))
        other_token = create_access_token(
            data={"sub": str(other_user.id), "username": other_user.username}
        )

        # Create spot as other user
        create_response = client.post(
            "/api/v1/skate-spots/",
            json=sample_spot_data,
            cookies={"access_token": other_token},
        )
        spot_id = create_response.json()["id"]

        # Try to delete as test_user
        delete_response = client.delete(
            f"/api/v1/skate-spots/{spot_id}",
            cookies={"access_token": auth_token},
        )

        assert delete_response.status_code == 403

    def test_admin_can_delete_any_spot(
        self, client, session_factory, test_user, auth_token, admin_token, sample_spot_data
    ):
        """Test that admins can delete any spot."""
        # Create spot as regular user
        create_response = client.post(
            "/api/v1/skate-spots/",
            json=sample_spot_data,
            cookies={"access_token": auth_token},
        )
        spot_id = create_response.json()["id"]

        # Delete as admin
        delete_response = client.delete(
            f"/api/v1/skate-spots/{spot_id}",
            cookies={"access_token": admin_token},
        )

        assert delete_response.status_code == 200

    def test_delete_spot_unauthenticated(self, client, test_user, auth_token, sample_spot_data):
        """Test that unauthenticated users cannot delete spots."""
        # Create a spot
        create_response = client.post(
            "/api/v1/skate-spots/",
            json=sample_spot_data,
            cookies={"access_token": auth_token},
        )
        spot_id = create_response.json()["id"]

        # Try to delete without authentication
        delete_response = client.delete(f"/api/v1/skate-spots/{spot_id}")

        assert delete_response.status_code == 401


class TestReadSpotsPublic:
    """Tests that reading spots doesn't require authentication."""

    def test_list_spots_unauthenticated(self, client):
        """Test that anyone can list spots."""
        response = client.get("/api/v1/skate-spots/")
        assert response.status_code == 200

    def test_get_spot_unauthenticated(self, client, test_user, auth_token, sample_spot_data):
        """Test that anyone can get a specific spot."""
        # Create a spot
        create_response = client.post(
            "/api/v1/skate-spots/",
            json=sample_spot_data,
            cookies={"access_token": auth_token},
        )
        spot_id = create_response.json()["id"]

        # Get without authentication
        response = client.get(f"/api/v1/skate-spots/{spot_id}")
        assert response.status_code == 200

    def test_get_geojson_unauthenticated(self, client):
        """Test that anyone can get spots as GeoJSON."""
        response = client.get("/api/v1/skate-spots/geojson")
        assert response.status_code == 200
