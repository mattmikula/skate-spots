"""Tests for root and documentation API endpoints."""


def test_root_endpoint(client):
    """Test the root endpoint returns HTML home page."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_openapi_json(client):
    """Test OpenAPI JSON endpoint."""
    response = client.get("/openapi.json")
    assert response.status_code == 200

    openapi_spec = response.json()
    assert openapi_spec["info"]["title"] == "Skate Spots API"
    assert openapi_spec["info"]["version"] == "0.1.0"

    # Check that our endpoints are documented
    paths = openapi_spec["paths"]
    assert "/api/v1/skate-spots/" in paths
    assert "/api/v1/skate-spots/{spot_id}" in paths


def test_docs_endpoint(client):
    """Test Swagger UI docs endpoint."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "swagger-ui" in response.text.lower()
    assert "Skate Spots API" in response.text
