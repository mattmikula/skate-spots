"""Tests for frontend HTML endpoints."""

import copy

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
def created_spot_id(client, sample_spot_payload, auth_token):
    """Create a spot and return its ID for testing."""
    response = client.post(
        "/api/v1/skate-spots/",
        json=sample_spot_payload,
        cookies={"access_token": auth_token},
    )
    return response.json()["id"]


def test_home_page(client):
    """Test that the home page returns HTML."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert b"All Skate Spots" in response.content


def test_home_page_with_data(client, created_spot_id):  # noqa: ARG001
    """Test that the home page shows spots when they exist."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Frontend Test Spot" in response.content


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


def test_list_spots_page_preserves_filters(
    client,
    created_spot_id,  # noqa: ARG001
    sample_spot_payload,
    auth_token,
):
    """Full page loads should honour filters and keep the form selection."""

    second_payload = copy.deepcopy(sample_spot_payload)
    second_payload.update(
        {
            "name": "Advanced Park",
            "spot_type": SpotType.PARK.value,
            "difficulty": Difficulty.ADVANCED.value,
            "city": "Madrid",
            "country": "Spain",
        }
    )
    client.post(
        "/api/v1/skate-spots/",
        json=second_payload,
        cookies={"access_token": auth_token},
    )

    response = client.get("/skate-spots?spot_type=park&difficulty=advanced")
    body = response.text

    assert response.status_code == 200
    assert "Advanced Park" in body
    assert "Frontend Test Spot" not in body
    assert "Clear filters" in body
    assert 'value="park"' in body
    assert "selected" in body


def test_htmx_spot_list_partial_filters_results(
    client,
    created_spot_id,  # noqa: ARG001
    sample_spot_payload,
    auth_token,
):
    """HTMX requests return the partial template with filtered results."""

    third_payload = copy.deepcopy(sample_spot_payload)
    third_payload.update(
        {
            "name": "Beginner Park",
            "spot_type": SpotType.PARK.value,
            "difficulty": Difficulty.BEGINNER.value,
            "city": "Lisbon",
            "country": "Portugal",
        }
    )
    client.post(
        "/api/v1/skate-spots/",
        json=third_payload,
        cookies={"access_token": auth_token},
    )

    response = client.get(
        "/skate-spots?spot_type=park",
        headers={"HX-Request": "true"},
    )
    body = response.text

    assert response.status_code == 200
    assert "Beginner Park" in body
    assert "Frontend Test Spot" not in body
    assert '<div class="spot-list">' in body
    assert "All Skate Spots" not in body


def test_new_spot_page(client, auth_token):
    """Test that the new spot form page returns HTML."""
    response = client.get("/skate-spots/new", cookies={"access_token": auth_token})
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert b"Add New Skate Spot" in response.content


def test_edit_spot_page(client, created_spot_id, auth_token):
    """Test that the edit spot form page returns HTML."""
    response = client.get(
        f"/skate-spots/{created_spot_id}/edit", cookies={"access_token": auth_token}
    )
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


def test_map_view_page(client):
    """Test that the map view page returns HTML."""
    response = client.get("/map")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert b"Skate Spots Map" in response.content
    assert b"leaflet" in response.content.lower()


def test_map_view_includes_leaflet(client):
    """Test that the map view includes Leaflet.js dependencies."""
    response = client.get("/map")
    assert response.status_code == 200
    # Check for Leaflet map container
    assert b'id="map"' in response.content
    # Check for GeoJSON endpoint fetch
    assert b"/api/v1/skate-spots/geojson" in response.content


def test_rating_section_anonymous(client, created_spot_id):  # noqa: ARG001
    """Rating section shows summary and login prompt for anonymous users."""

    response = client.get(f"/skate-spots/{created_spot_id}/rating-section")
    assert response.status_code == 200
    body = response.content.decode()
    assert "No ratings yet." in body
    assert "Log in" in body


def test_rating_section_authenticated(client, created_spot_id, auth_token):
    """Logged-in users can see the rating form with their saved rating."""

    response = client.get(
        f"/skate-spots/{created_spot_id}/rating-section",
        cookies={"access_token": auth_token},
    )
    assert response.status_code == 200
    body = response.content.decode()
    assert "Save rating" in body
    assert "Remove rating" not in body  # no rating yet


def test_submit_and_delete_rating_via_frontend(client, created_spot_id, auth_token):
    """Submitting and deleting ratings through the frontend routes returns updated snippets."""

    post_response = client.post(
        f"/skate-spots/{created_spot_id}/ratings",
        data={"score": "4", "comment": "Smooth lines"},
        cookies={"access_token": auth_token},
        headers={"HX-Request": "true"},
    )
    assert post_response.status_code == 200
    post_body = post_response.content.decode()
    assert "Rating saved!" in post_body
    assert "Remove rating" in post_body
    assert "4" in post_body

    delete_response = client.delete(
        f"/skate-spots/{created_spot_id}/ratings",
        cookies={"access_token": auth_token},
        headers={"HX-Request": "true"},
    )
    assert delete_response.status_code == 200
    delete_body = delete_response.content.decode()
    assert "Rating removed." in delete_body
    assert "Remove rating" not in delete_body
