"""Tests for API endpoints."""

import pytest
from django.contrib.auth import get_user_model
from spots.models import Difficulty, SkateSpot, SpotType

User = get_user_model()


class TestAuthEndpoints:
    """Tests for authentication endpoints."""

    @pytest.mark.django_db
    def test_register_success(self, api_client):
        """Test successful user registration."""
        response = api_client.post(
            "/api/v1/auth/register/",
            {
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "newpass123",
            },
            format="json"
        )
        assert response.status_code == 201
        assert response.data["username"] == "newuser"
        assert response.data["email"] == "newuser@example.com"

    @pytest.mark.django_db
    def test_register_duplicate_email(self, api_client, test_user):
        """Test registration with duplicate email fails."""
        response = api_client.post(
            "/api/v1/auth/register/",
            {
                "email": test_user.email,
                "username": "newuser",
                "password": "newpass123",
            },
            format="json"
        )
        assert response.status_code == 400
        # Check for either custom or Django's error message
        assert "email" in str(response.data).lower() or "Email already registered" in str(response.data)

    @pytest.mark.django_db
    def test_register_duplicate_username(self, api_client, test_user):
        """Test registration with duplicate username fails."""
        response = api_client.post(
            "/api/v1/auth/register/",
            {
                "email": "different@example.com",
                "username": test_user.username,
                "password": "newpass123",
            },
            format="json"
        )
        assert response.status_code == 400
        # Check for either custom or Django's error message
        assert "username" in str(response.data).lower() or "Username already taken" in str(response.data)

    @pytest.mark.django_db
    def test_login_success(self, api_client, test_user):
        """Test successful login."""
        response = api_client.post(
            "/api/v1/auth/login/",
            {
                "username": test_user.username,
                "password": "testpass123",
            },
            format="json"
        )
        assert response.status_code == 200
        assert "access_token" in response.data

    @pytest.mark.django_db
    def test_login_invalid_credentials(self, api_client, test_user):
        """Test login with invalid credentials fails."""
        response = api_client.post(
            "/api/v1/auth/login/",
            {
                "username": test_user.username,
                "password": "wrongpassword",
            },
            format="json"
        )
        assert response.status_code == 401
        assert "Incorrect username or password" in str(response.data)

    @pytest.mark.django_db
    def test_get_current_user(self, authenticated_api_client, test_user):
        """Test getting current user info."""
        response = authenticated_api_client.get("/api/v1/auth/me/")
        assert response.status_code == 200
        assert response.data["username"] == test_user.username
        assert response.data["email"] == test_user.email

    @pytest.mark.django_db
    def test_get_current_user_unauthenticated(self, api_client):
        """Test getting current user without auth fails."""
        response = api_client.get("/api/v1/auth/me/")
        assert response.status_code == 401

    @pytest.mark.django_db
    def test_logout(self, authenticated_api_client):
        """Test logout endpoint."""
        response = authenticated_api_client.post("/api/v1/auth/logout/")
        assert response.status_code == 200


class TestSkateSpotListEndpoint:
    """Tests for skate spot list endpoint."""

    @pytest.mark.django_db
    def test_list_spots_empty(self, api_client):
        """Test listing spots when none exist."""
        response = api_client.get("/api/v1/skate-spots/")
        assert response.status_code == 200
        assert response.data == []

    @pytest.mark.django_db
    def test_list_spots_with_data(self, api_client, test_user):
        """Test listing spots with data."""
        SkateSpot.objects.create(
            name="Spot 1",
            description="First spot",
            spot_type=SpotType.PARK,
            difficulty=Difficulty.BEGINNER,
            latitude=40.7128,
            longitude=-74.0060,
            city="New York",
            country="USA",
            owner=test_user
        )
        SkateSpot.objects.create(
            name="Spot 2",
            description="Second spot",
            spot_type=SpotType.STREET,
            difficulty=Difficulty.ADVANCED,
            latitude=34.0522,
            longitude=-118.2437,
            city="Los Angeles",
            country="USA",
            owner=test_user
        )
        response = api_client.get("/api/v1/skate-spots/")
        assert response.status_code == 200
        assert len(response.data) == 2

    @pytest.mark.django_db
    def test_list_spots_filter_by_city(self, api_client, test_user):
        """Test filtering spots by city."""
        SkateSpot.objects.create(
            name="NYC Spot",
            description="In New York",
            spot_type=SpotType.PARK,
            difficulty=Difficulty.BEGINNER,
            latitude=40.7128,
            longitude=-74.0060,
            city="New York",
            country="USA",
            owner=test_user
        )
        SkateSpot.objects.create(
            name="LA Spot",
            description="In Los Angeles",
            spot_type=SpotType.STREET,
            difficulty=Difficulty.BEGINNER,
            latitude=34.0522,
            longitude=-118.2437,
            city="Los Angeles",
            country="USA",
            owner=test_user
        )
        response = api_client.get("/api/v1/skate-spots/?city=New%20York")
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["name"] == "NYC Spot"

    @pytest.mark.django_db
    def test_list_spots_filter_by_difficulty(self, api_client, test_user):
        """Test filtering spots by difficulty."""
        SkateSpot.objects.create(
            name="Easy Spot",
            description="Easy",
            spot_type=SpotType.PARK,
            difficulty=Difficulty.BEGINNER,
            latitude=40.7128,
            longitude=-74.0060,
            city="New York",
            country="USA",
            owner=test_user
        )
        SkateSpot.objects.create(
            name="Hard Spot",
            description="Hard",
            spot_type=SpotType.PARK,
            difficulty=Difficulty.EXPERT,
            latitude=34.0522,
            longitude=-118.2437,
            city="Los Angeles",
            country="USA",
            owner=test_user
        )
        response = api_client.get("/api/v1/skate-spots/?difficulty=expert")
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["difficulty"] == "expert"

    @pytest.mark.django_db
    def test_list_spots_filter_by_type(self, api_client, test_user):
        """Test filtering spots by type."""
        SkateSpot.objects.create(
            name="Park Spot",
            description="Park",
            spot_type=SpotType.PARK,
            difficulty=Difficulty.BEGINNER,
            latitude=40.7128,
            longitude=-74.0060,
            city="New York",
            country="USA",
            owner=test_user
        )
        SkateSpot.objects.create(
            name="Street Spot",
            description="Street",
            spot_type=SpotType.STREET,
            difficulty=Difficulty.BEGINNER,
            latitude=34.0522,
            longitude=-118.2437,
            city="Los Angeles",
            country="USA",
            owner=test_user
        )
        response = api_client.get("/api/v1/skate-spots/?spot_type=park")
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["spot_type"] == "park"


class TestSkateSpotCreateEndpoint:
    """Tests for creating skate spots."""

    @pytest.mark.django_db
    def test_create_spot_success(self, authenticated_api_client):
        """Test creating a spot with authentication."""
        response = authenticated_api_client.post(
            "/api/v1/skate-spots/",
            {
                "name": "New Spot",
                "description": "A brand new spot",
                "spot_type": "park",
                "difficulty": "intermediate",
                "location": {
                    "latitude": 40.7128,
                    "longitude": -74.0060,
                    "city": "New York",
                    "country": "USA",
                },
                "is_public": True,
                "requires_permission": False,
            },
            format="json"
        )
        assert response.status_code == 201
        assert response.data["name"] == "New Spot"
        assert SkateSpot.objects.count() == 1

    @pytest.mark.django_db
    def test_create_spot_unauthenticated(self, api_client):
        """Test creating a spot without authentication fails."""
        response = api_client.post(
            "/api/v1/skate-spots/",
            {
                "name": "New Spot",
                "description": "A spot",
                "spot_type": "park",
                "difficulty": "intermediate",
                "location": {
                    "latitude": 40.7128,
                    "longitude": -74.0060,
                    "city": "New York",
                    "country": "USA",
                },
                "is_public": True,
                "requires_permission": False,
            },
            format="json"
        )
        assert response.status_code == 401
        assert SkateSpot.objects.count() == 0

    @pytest.mark.django_db
    def test_create_spot_invalid_latitude(self, authenticated_api_client):
        """Test creating a spot with invalid latitude fails."""
        response = authenticated_api_client.post(
            "/api/v1/skate-spots/",
            {
                "name": "New Spot",
                "description": "A spot",
                "spot_type": "park",
                "difficulty": "intermediate",
                "location": {
                    "latitude": 91,  # Invalid
                    "longitude": -74.0060,
                    "city": "New York",
                    "country": "USA",
                },
                "is_public": True,
                "requires_permission": False,
            },
            format="json"
        )
        assert response.status_code == 400

    @pytest.mark.django_db
    def test_create_spot_missing_flat_location_fields(self, authenticated_api_client):
        """Flat payloads without full location data should return validation errors."""
        response = authenticated_api_client.post(
            "/api/v1/skate-spots/",
            {
                "name": "Partial Location Spot",
                "description": "Missing some location fields",
                "spot_type": "park",
                "difficulty": "intermediate",
                "latitude": 40.7128,
                "is_public": True,
                "requires_permission": False,
            },
            format="json"
        )

        assert response.status_code == 400
        assert "longitude" in response.data
        assert "city" in response.data
        assert "country" in response.data

    @pytest.mark.django_db
    def test_create_spot_with_flat_location_fields(self, authenticated_api_client):
        """Flat payloads with full location data should be accepted."""
        response = authenticated_api_client.post(
            "/api/v1/skate-spots/",
            {
                "name": "Flat Location Spot",
                "description": "Using flat location fields",
                "spot_type": "street",
                "difficulty": "beginner",
                "latitude": 34.0522,
                "longitude": -118.2437,
                "city": "Los Angeles",
                "country": "USA",
                "address": "123 Skate Park",
                "is_public": False,
                "requires_permission": True,
            },
            format="json"
        )

        assert response.status_code == 201
        assert response.data["name"] == "Flat Location Spot"
        assert response.data["location"]["city"] == "Los Angeles"


class TestSkateSpotDetailEndpoint:
    """Tests for retrieving single skate spot."""

    @pytest.mark.django_db
    def test_get_spot_success(self, api_client, test_user):
        """Test getting a single spot."""
        spot = SkateSpot.objects.create(
            name="Test Spot",
            description="A test spot",
            spot_type=SpotType.PARK,
            difficulty=Difficulty.BEGINNER,
            latitude=40.7128,
            longitude=-74.0060,
            city="New York",
            country="USA",
            owner=test_user
        )
        response = api_client.get(f"/api/v1/skate-spots/{spot.id}/")
        assert response.status_code == 200
        assert response.data["name"] == "Test Spot"

    @pytest.mark.django_db
    def test_get_spot_not_found(self, api_client):
        """Test getting non-existent spot fails."""
        response = api_client.get("/api/v1/skate-spots/00000000-0000-0000-0000-000000000000/")
        assert response.status_code == 404


class TestGeoJSONEndpoint:
    """Tests for GeoJSON endpoint."""

    @pytest.mark.django_db
    def test_geojson_empty(self, api_client):
        """Test GeoJSON with no spots."""
        response = api_client.get("/api/v1/skate-spots/geojson/")
        assert response.status_code == 200
        assert response.data["type"] == "FeatureCollection"
        assert response.data["features"] == []

    @pytest.mark.django_db
    def test_geojson_with_spots(self, api_client, test_user):
        """Test GeoJSON with spots."""
        SkateSpot.objects.create(
            name="Test Spot",
            description="A test spot",
            spot_type=SpotType.PARK,
            difficulty=Difficulty.BEGINNER,
            latitude=40.7128,
            longitude=-74.0060,
            city="New York",
            country="USA",
            owner=test_user
        )
        response = api_client.get("/api/v1/skate-spots/geojson/")
        assert response.status_code == 200
        assert response.data["type"] == "FeatureCollection"
        assert len(response.data["features"]) == 1
        assert response.data["features"][0]["type"] == "Feature"
        assert response.data["features"][0]["geometry"]["type"] == "Point"


class TestSkateSpotUpdateEndpoint:
    """Tests for updating skate spots."""

    @pytest.mark.django_db
    def test_update_spot_by_owner(self, authenticated_api_client, test_user):
        """Test updating a spot as the owner."""
        spot = SkateSpot.objects.create(
            name="Original Spot",
            description="Original description",
            spot_type=SpotType.PARK,
            difficulty=Difficulty.BEGINNER,
            latitude=40.7128,
            longitude=-74.0060,
            city="New York",
            country="USA",
            owner=test_user
        )
        response = authenticated_api_client.patch(
            f"/api/v1/skate-spots/{spot.id}/",
            {
                "name": "Updated Spot",
                "description": "Updated description",
            },
            format="json"
        )
        assert response.status_code == 200
        assert response.data["name"] == "Updated Spot"
        spot.refresh_from_db()
        assert spot.name == "Updated Spot"

    @pytest.mark.django_db
    def test_update_spot_by_non_owner(self, api_client, test_user, another_user):
        """Test updating a spot as non-owner fails."""
        spot = SkateSpot.objects.create(
            name="Original Spot",
            description="Original description",
            spot_type=SpotType.PARK,
            difficulty=Difficulty.BEGINNER,
            latitude=40.7128,
            longitude=-74.0060,
            city="New York",
            country="USA",
            owner=test_user
        )
        # Authenticate as another_user
        api_client.force_authenticate(user=another_user)
        response = api_client.patch(
            f"/api/v1/skate-spots/{spot.id}/",
            {
                "name": "Hacked Spot",
            },
            format="json"
        )
        assert response.status_code == 403
        spot.refresh_from_db()
        assert spot.name == "Original Spot"

    @pytest.mark.django_db
    def test_update_spot_unauthenticated(self, api_client, test_user):
        """Test updating a spot without authentication fails."""
        spot = SkateSpot.objects.create(
            name="Original Spot",
            description="Original description",
            spot_type=SpotType.PARK,
            difficulty=Difficulty.BEGINNER,
            latitude=40.7128,
            longitude=-74.0060,
            city="New York",
            country="USA",
            owner=test_user
        )
        response = api_client.patch(
            f"/api/v1/skate-spots/{spot.id}/",
            {
                "name": "Updated Spot",
            },
            format="json"
        )
        assert response.status_code == 401

    @pytest.mark.django_db
    def test_update_spot_by_admin(self, admin_api_client, test_user):
        """Test updating a spot as admin succeeds."""
        spot = SkateSpot.objects.create(
            name="Original Spot",
            description="Original description",
            spot_type=SpotType.PARK,
            difficulty=Difficulty.BEGINNER,
            latitude=40.7128,
            longitude=-74.0060,
            city="New York",
            country="USA",
            owner=test_user
        )
        response = admin_api_client.patch(
            f"/api/v1/skate-spots/{spot.id}/",
            {
                "name": "Admin Updated Spot",
            },
            format="json"
        )
        assert response.status_code == 200
        assert response.data["name"] == "Admin Updated Spot"


class TestSkateSpotDeleteEndpoint:
    """Tests for deleting skate spots."""

    @pytest.mark.django_db
    def test_delete_spot_by_owner(self, authenticated_api_client, test_user):
        """Test deleting a spot as the owner."""
        spot = SkateSpot.objects.create(
            name="Spot to Delete",
            description="To be deleted",
            spot_type=SpotType.PARK,
            difficulty=Difficulty.BEGINNER,
            latitude=40.7128,
            longitude=-74.0060,
            city="New York",
            country="USA",
            owner=test_user
        )
        spot_id = spot.id
        response = authenticated_api_client.delete(f"/api/v1/skate-spots/{spot.id}/")
        assert response.status_code == 204
        assert not SkateSpot.objects.filter(id=spot_id).exists()

    @pytest.mark.django_db
    def test_delete_spot_by_non_owner(self, api_client, test_user, another_user):
        """Test deleting a spot as non-owner fails."""
        spot = SkateSpot.objects.create(
            name="Spot to Delete",
            description="To be deleted",
            spot_type=SpotType.PARK,
            difficulty=Difficulty.BEGINNER,
            latitude=40.7128,
            longitude=-74.0060,
            city="New York",
            country="USA",
            owner=test_user
        )
        # Authenticate as another_user
        api_client.force_authenticate(user=another_user)
        response = api_client.delete(f"/api/v1/skate-spots/{spot.id}/")
        assert response.status_code == 403
        assert SkateSpot.objects.filter(id=spot.id).exists()

    @pytest.mark.django_db
    def test_delete_spot_unauthenticated(self, api_client, test_user):
        """Test deleting a spot without authentication fails."""
        spot = SkateSpot.objects.create(
            name="Spot to Delete",
            description="To be deleted",
            spot_type=SpotType.PARK,
            difficulty=Difficulty.BEGINNER,
            latitude=40.7128,
            longitude=-74.0060,
            city="New York",
            country="USA",
            owner=test_user
        )
        response = api_client.delete(f"/api/v1/skate-spots/{spot.id}/")
        assert response.status_code == 401
        assert SkateSpot.objects.filter(id=spot.id).exists()

    @pytest.mark.django_db
    def test_delete_spot_by_admin(self, admin_api_client, test_user):
        """Test deleting a spot as admin succeeds."""
        spot = SkateSpot.objects.create(
            name="Spot to Delete",
            description="To be deleted",
            spot_type=SpotType.PARK,
            difficulty=Difficulty.BEGINNER,
            latitude=40.7128,
            longitude=-74.0060,
            city="New York",
            country="USA",
            owner=test_user
        )
        spot_id = spot.id
        response = admin_api_client.delete(f"/api/v1/skate-spots/{spot.id}/")
        assert response.status_code == 204
        assert not SkateSpot.objects.filter(id=spot_id).exists()
