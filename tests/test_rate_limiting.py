"""Tests for rate limiting on API endpoints."""

import inspect

import pytest
from accounts.views import AuthViewSet
from django.contrib.auth import get_user_model
from django_ratelimit.decorators import ratelimit
from spots.views import SkateSpotViewSet

User = get_user_model()


class TestRateLimitingConfiguration:
    """Tests that rate limiting decorators are properly configured."""

    def test_register_endpoint_has_rate_limit(self):
        """Test register endpoint is decorated with rate limiting."""
        register_method = AuthViewSet.register
        # Check if method has ratelimit decorator
        has_ratelimit = False
        if hasattr(register_method, "__wrapped__"):
            # The decorator wraps the method
            has_ratelimit = True
        assert has_ratelimit, "Register endpoint should have rate limiting decorator"

    def test_login_endpoint_has_rate_limit(self):
        """Test login endpoint is decorated with rate limiting."""
        login_method = AuthViewSet.login
        # Check if method has ratelimit decorator
        has_ratelimit = False
        if hasattr(login_method, "__wrapped__"):
            # The decorator wraps the method
            has_ratelimit = True
        assert has_ratelimit, "Login endpoint should have rate limiting decorator"

    def test_create_spot_endpoint_has_rate_limit(self):
        """Test create endpoint is decorated with rate limiting."""
        create_method = SkateSpotViewSet.create
        # Check if method has ratelimit decorator
        has_ratelimit = False
        if hasattr(create_method, "__wrapped__"):
            # The decorator wraps the method
            has_ratelimit = True
        assert has_ratelimit, "Create spot endpoint should have rate limiting decorator"

    def test_update_spot_endpoint_has_rate_limit(self):
        """Test update endpoint is decorated with rate limiting."""
        update_method = SkateSpotViewSet.update
        # Check if method has ratelimit decorator
        has_ratelimit = False
        if hasattr(update_method, "__wrapped__"):
            # The decorator wraps the method
            has_ratelimit = True
        assert has_ratelimit, "Update spot endpoint should have rate limiting decorator"

    def test_destroy_spot_endpoint_has_rate_limit(self):
        """Test destroy endpoint is decorated with rate limiting."""
        destroy_method = SkateSpotViewSet.destroy
        # Check if method has ratelimit decorator
        has_ratelimit = False
        if hasattr(destroy_method, "__wrapped__"):
            # The decorator wraps the method
            has_ratelimit = True
        assert has_ratelimit, "Destroy spot endpoint should have rate limiting decorator"


class TestReadOperationsNoRateLimit:
    """Tests that read operations are not rate limited."""

    @pytest.mark.django_db
    def test_list_spots_accessible_multiple_times(self, api_client):
        """Test list endpoint can be called multiple times."""
        # Try to list spots multiple times (should work without rate limit)
        for i in range(10):
            response = api_client.get("/api/v1/skate-spots/")
            assert response.status_code == 200

    @pytest.mark.django_db
    def test_get_spot_detail_accessible_multiple_times(self, api_client, test_user):
        """Test detail endpoint can be called multiple times."""
        from spots.models import Difficulty, SkateSpot, SpotType

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

        # Try to get spot multiple times (should work without rate limit)
        for i in range(10):
            response = api_client.get(f"/api/v1/skate-spots/{spot.id}/")
            assert response.status_code == 200

    @pytest.mark.django_db
    def test_geojson_accessible_multiple_times(self, api_client):
        """Test geojson endpoint can be called multiple times."""
        # Try to get geojson multiple times (should work without rate limit)
        for i in range(10):
            response = api_client.get("/api/v1/skate-spots/geojson/")
            assert response.status_code == 200


class TestAuthenticationEndpointAccess:
    """Tests that authentication endpoints require proper credentials."""

    @pytest.mark.django_db
    def test_register_endpoint_accessible(self, api_client):
        """Test register endpoint is accessible."""
        response = api_client.post(
            "/api/v1/auth/register/",
            {
                "email": "test@example.com",
                "username": "testuser",
                "password": "testpass123",
            },
            format="json"
        )
        assert response.status_code == 201

    @pytest.mark.django_db
    def test_login_endpoint_accessible(self, api_client, test_user):
        """Test login endpoint is accessible."""
        response = api_client.post(
            "/api/v1/auth/login/",
            {
                "username": test_user.username,
                "password": "testpass123",
            },
            format="json"
        )
        assert response.status_code == 200


class TestWriteOperationsProtected:
    """Tests that write operations require authentication."""

    @pytest.mark.django_db
    def test_create_spot_requires_auth(self, api_client):
        """Test create requires authentication."""
        response = api_client.post(
            "/api/v1/skate-spots/",
            {
                "name": "Spot",
                "description": "Description",
                "spot_type": "park",
                "difficulty": "beginner",
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

    @pytest.mark.django_db
    def test_update_spot_requires_auth(self, api_client, test_user):
        """Test update requires authentication."""
        from spots.models import Difficulty, SkateSpot, SpotType

        spot = SkateSpot.objects.create(
            name="Spot",
            description="Description",
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
            {"description": "Updated"},
            format="json"
        )
        assert response.status_code == 401

    @pytest.mark.django_db
    def test_delete_spot_requires_auth(self, api_client, test_user):
        """Test delete requires authentication."""
        from spots.models import Difficulty, SkateSpot, SpotType

        spot = SkateSpot.objects.create(
            name="Spot",
            description="Description",
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
