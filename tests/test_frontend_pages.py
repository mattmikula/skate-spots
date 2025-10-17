"""Tests for frontend HTML pages."""

import pytest
from django.contrib.auth import get_user_model
from spots.models import Difficulty, SkateSpot, SpotType

User = get_user_model()


class TestFrontendPages:
    """Tests for frontend HTML pages."""

    @pytest.mark.django_db
    def test_home_page_loads(self, client):
        """Test home page loads."""
        response = client.get("/")
        assert response.status_code == 200
        assert b"Skate Spots" in response.content

    @pytest.mark.django_db
    def test_home_page_displays_spots(self, client, test_user):
        """Test home page displays spots."""
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
        response = client.get("/")
        assert response.status_code == 200
        assert b"Test Spot" in response.content

    @pytest.mark.django_db
    def test_spots_list_page(self, client):
        """Test spots list page."""
        response = client.get("/skate-spots/")
        assert response.status_code == 200
        assert b"All Skate Spots" in response.content or b"Skate Spots" in response.content

    @pytest.mark.django_db
    def test_map_page(self, client):
        """Test map page."""
        response = client.get("/map/")
        assert response.status_code == 200
        assert b"map" in response.content.lower()

    @pytest.mark.django_db
    def test_login_page_loads(self, client):
        """Test login page loads."""
        response = client.get("/login/")
        assert response.status_code == 200
        assert b"Login" in response.content or b"login" in response.content

    @pytest.mark.django_db
    def test_register_page_loads(self, client):
        """Test register page loads."""
        response = client.get("/register/")
        assert response.status_code == 200
        assert b"Register" in response.content or b"register" in response.content

    @pytest.mark.django_db
    def test_new_spot_page_requires_auth(self, client):
        """Test new spot page requires authentication."""
        response = client.get("/skate-spots/new/")
        assert response.status_code == 302  # Redirect to login

    @pytest.mark.django_db
    def test_new_spot_page_authenticated(self, client, test_user):
        """Test new spot page loads when authenticated."""
        client.force_login(test_user)
        response = client.get("/skate-spots/new/")
        assert response.status_code == 200
        assert b"form" in response.content.lower() or b"new" in response.content.lower()

    @pytest.mark.django_db
    def test_edit_spot_page_requires_auth(self, client, test_user):
        """Test edit spot page requires authentication."""
        spot = SkateSpot.objects.create(
            name="Test Spot",
            description="Test",
            spot_type=SpotType.PARK,
            difficulty=Difficulty.BEGINNER,
            latitude=40.7128,
            longitude=-74.0060,
            city="New York",
            country="USA",
            owner=test_user
        )
        response = client.get(f"/skate-spots/{spot.id}/edit/")
        assert response.status_code == 302  # Redirect to login

    @pytest.mark.django_db
    def test_edit_spot_page_owner_only(self, client, test_user, another_user):
        """Test edit spot page only accessible to owner."""
        spot = SkateSpot.objects.create(
            name="Test Spot",
            description="Test",
            spot_type=SpotType.PARK,
            difficulty=Difficulty.BEGINNER,
            latitude=40.7128,
            longitude=-74.0060,
            city="New York",
            country="USA",
            owner=test_user
        )
        client.force_login(another_user)
        response = client.get(f"/skate-spots/{spot.id}/edit/")
        assert response.status_code == 302  # Redirect (not owner)

    @pytest.mark.django_db
    def test_edit_spot_page_owner_access(self, client, test_user):
        """Test edit spot page accessible to owner."""
        spot = SkateSpot.objects.create(
            name="Test Spot",
            description="Test",
            spot_type=SpotType.PARK,
            difficulty=Difficulty.BEGINNER,
            latitude=40.7128,
            longitude=-74.0060,
            city="New York",
            country="USA",
            owner=test_user
        )
        client.force_login(test_user)
        response = client.get(f"/skate-spots/{spot.id}/edit/")
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_authenticated_user_redirect_login(self, client, test_user):
        """Test authenticated users are redirected from login page."""
        client.force_login(test_user)
        response = client.get("/login/")
        assert response.status_code == 302  # Redirect to home

    @pytest.mark.django_db
    def test_authenticated_user_redirect_register(self, client, test_user):
        """Test authenticated users are redirected from register page."""
        client.force_login(test_user)
        response = client.get("/register/")
        assert response.status_code == 302  # Redirect to home


class TestFormSubmissions:
    """Tests for form submissions."""

    @pytest.mark.django_db
    def test_register_form_submission_success(self, client):
        """Test successful user registration via form."""
        response = client.post(
            "/register/",
            {
                "email": "newuser@example.com",
                "username": "newuser",
                "password1": "testpass123secure",
                "password2": "testpass123secure",
            }
        )
        # Should redirect to login after successful registration
        assert response.status_code == 302
        assert User.objects.filter(username="newuser").exists()

    @pytest.mark.django_db
    def test_register_form_submission_password_mismatch(self, client):
        """Test registration fails with mismatched passwords."""
        response = client.post(
            "/register/",
            {
                "email": "newuser@example.com",
                "username": "newuser",
                "password1": "testpass123secure",
                "password2": "differentpass123",
            }
        )
        # Should not redirect (form error)
        assert response.status_code == 200
        assert not User.objects.filter(username="newuser").exists()

    @pytest.mark.django_db
    def test_login_form_submission_success(self, client, test_user):
        """Test successful login via form."""
        response = client.post(
            "/login/",
            {
                "username": test_user.username,
                "password": "testpass123",
            }
        )
        # Should redirect to home after successful login
        assert response.status_code == 302
        # Check user is in session
        assert "_auth_user_id" in client.session

    @pytest.mark.django_db
    def test_login_form_submission_invalid_credentials(self, client, test_user):
        """Test login fails with invalid credentials."""
        response = client.post(
            "/login/",
            {
                "username": test_user.username,
                "password": "wrongpassword",
            }
        )
        # Should not redirect (form error)
        assert response.status_code == 200
        assert "_auth_user_id" not in client.session

    @pytest.mark.django_db
    def test_create_spot_form_submission_success(self, client, test_user):
        """Test successful spot creation via form."""
        client.force_login(test_user)
        response = client.post(
            "/skate-spots/new/",
            {
                "name": "New Spot",
                "description": "A new spot",
                "spot_type": SpotType.PARK,
                "difficulty": Difficulty.BEGINNER,
                "latitude": "40.7128",
                "longitude": "-74.0060",
                "address": "123 Skate St",
                "city": "New York",
                "country": "USA",
            }
        )
        # Should redirect to spot detail page
        assert response.status_code == 302
        assert SkateSpot.objects.filter(name="New Spot").exists()
        spot = SkateSpot.objects.get(name="New Spot")
        assert spot.owner == test_user

    @pytest.mark.django_db
    def test_create_spot_form_submission_invalid_latitude(self, client, test_user):
        """Test spot creation fails with invalid latitude."""
        client.force_login(test_user)
        response = client.post(
            "/skate-spots/new/",
            {
                "name": "New Spot",
                "description": "A new spot",
                "spot_type": SpotType.PARK,
                "difficulty": Difficulty.BEGINNER,
                "latitude": "91",  # Invalid
                "longitude": "-74.0060",
                "address": "123 Skate St",
                "city": "New York",
                "country": "USA",
            }
        )
        # Should not redirect (form error)
        assert response.status_code == 200
        assert not SkateSpot.objects.filter(name="New Spot").exists()

    @pytest.mark.django_db
    def test_edit_spot_form_submission_success(self, client, test_user):
        """Test successful spot editing via form."""
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
        client.force_login(test_user)
        response = client.post(
            f"/skate-spots/{spot.id}/edit/",
            {
                "name": "Updated Spot",
                "description": "Updated description",
                "spot_type": SpotType.STREET,
                "difficulty": Difficulty.INTERMEDIATE,
                "latitude": "40.7128",
                "longitude": "-74.0060",
                "address": "456 Skate Ave",
                "city": "New York",
                "country": "USA",
            }
        )
        # Should redirect to spot detail or list
        assert response.status_code == 302
        spot.refresh_from_db()
        assert spot.name == "Updated Spot"
        assert spot.description == "Updated description"
        assert spot.spot_type == SpotType.STREET

    @pytest.mark.django_db
    def test_logout_form_submission(self, client, test_user):
        """Test logout via form submission."""
        client.force_login(test_user)
        assert "_auth_user_id" in client.session
        response = client.post("/logout/")
        # Should redirect to home
        assert response.status_code == 302
        # User should be logged out
        assert "_auth_user_id" not in client.session
