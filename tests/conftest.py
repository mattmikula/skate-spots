"""Shared test fixtures and configuration for pytest-django."""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def client():
    """Django test client."""
    return Client()


@pytest.fixture
def api_client():
    """DRF API test client."""
    return APIClient()


@pytest.fixture
def test_user(db):
    """Create a test user."""
    return User.objects.create_user(
        email="test@example.com",
        username="testuser",
        password="testpass123"
    )


@pytest.fixture
def authenticated_user(test_user):
    """Return authenticated test user."""
    return test_user


@pytest.fixture
def authenticated_api_client(api_client, test_user):
    """API client authenticated as test user."""
    from rest_framework_simplejwt.tokens import RefreshToken

    refresh = RefreshToken.for_user(test_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
    return api_client


@pytest.fixture
def another_user(db):
    """Create another test user for permission tests."""
    return User.objects.create_user(
        email="other@example.com",
        username="otheruser",
        password="otherpass123"
    )


@pytest.fixture
def admin_user(db):
    """Create an admin user."""
    user = User.objects.create_user(
        email="admin@example.com",
        username="admin",
        password="adminpass123"
    )
    user.is_admin = True
    user.is_staff = True
    user.is_superuser = True
    user.save()
    return user


@pytest.fixture
def admin_api_client(api_client, admin_user):
    """API client authenticated as admin."""
    from rest_framework_simplejwt.tokens import RefreshToken

    refresh = RefreshToken.for_user(admin_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
    return api_client
