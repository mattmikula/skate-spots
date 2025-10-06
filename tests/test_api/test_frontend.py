"""Tests for frontend HTML endpoints."""

import pytest

from app.models.skate_spot import Difficulty, SpotType


@pytest.fixture
def sample_spot_payload():
    """Sample payload for creating a skate spot."""
    return {
        "name": "Frontend Test Spot",
        "description": "A spot for testing frontend routes",
        "spot_type": SpotType.STREET.value,
        "difficulty": Difficulty.BEGINNER.value,
        "location": {
            "latitude": 37.7749,
            "longitude": -122.4194,
            "address": "789 Frontend Ave",
            "city": "San Francisco",
            "country": "USA",
        },
        "is_public": True,
        "requires_permission": False,
    }


@pytest.fixture
def created_spot_id(client, sample_spot_payload):
    """Create a spot and return its ID for testing."""
    response = client.post("/api/v1/skate-spots/", json=sample_spot_payload)
    return response.json()["id"]


def test_home_page(client):
    """Test that the home page returns HTML."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_list_spots_page(client):
    """Test that the skate spots list page returns HTML."""
    response = client.get("/skate-spots")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert b"All Skate Spots" in response.content


def test_list_spots_page_with_data(client, created_spot_id):  # noqa: ARG001
    """Test that the skate spots list page shows spots."""
    response = client.get("/skate-spots")
    assert response.status_code == 200
    assert b"Frontend Test Spot" in response.content


def test_new_spot_page(client):
    """Test that the new spot form page returns HTML."""
    response = client.get("/skate-spots/new")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert b"Add New Skate Spot" in response.content


def test_edit_spot_page(client, created_spot_id):
    """Test that the edit spot form page returns HTML."""
    response = client.get(f"/skate-spots/{created_spot_id}/edit")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert b"Edit Skate Spot" in response.content
    assert b"Frontend Test Spot" in response.content


def test_edit_spot_page_nonexistent(client):
    """Test that editing a non-existent spot returns error."""
    from uuid import uuid4

    fake_id = str(uuid4())
    response = client.get(f"/skate-spots/{fake_id}/edit")
    # The page should still render, but the spot will be None
    assert response.status_code == 200
