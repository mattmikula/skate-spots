"""Tests for API endpoints."""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from spots.models import SkateSpot

User = get_user_model()


@pytest.mark.django_db
def test_list_spots():
    """Test listing skate spots via API."""
    client = Client()
    response = client.get("/api/v1/skate-spots/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_register_user():
    """Test user registration via API."""
    client = Client()
    response = client.post(
        "/api/v1/auth/register/",
        {
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpass123",
        },
        content_type="application/json",
    )
    assert response.status_code == 201
    assert User.objects.filter(username="testuser").exists()


@pytest.mark.django_db
def test_create_spot():
    """Test creating a skate spot requires authentication."""
    client = Client()
    response = client.post(
        "/api/v1/skate-spots/",
        {
            "name": "Test Spot",
            "description": "A test spot",
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
        content_type="application/json",
    )
    # Should fail without authentication
    assert response.status_code == 401


@pytest.mark.django_db
def test_home_page():
    """Test home page loads."""
    client = Client()
    response = client.get("/")
    assert response.status_code == 200
    assert b"Skate Spots" in response.content


@pytest.mark.django_db
def test_login_page():
    """Test login page loads."""
    client = Client()
    response = client.get("/login/")
    assert response.status_code == 200
    assert b"Login" in response.content
