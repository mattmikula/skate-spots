"""Tests for skate spot location validation."""



def test_create_spot_with_empty_coordinates(client, auth_token):
    """API rejects spot creation when coordinates are not provided."""
    # Arrange
    form_data = {
        "name": "Test Spot",
        "description": "Test description",
        "spot_type": "street",
        "difficulty": "beginner",
        "latitude": "",  # Empty coordinate
        "longitude": "",  # Empty coordinate
        "city": "Test City",
        "country": "Test Country",
        "is_public": "true",
    }

    # Act
    response = client.post(
        "/api/v1/skate-spots/",
        data=form_data,
        cookies={"access_token": auth_token},
    )

    # Assert
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "Location coordinates are required" in str(detail) or "required" in str(detail).lower()


def test_create_spot_with_invalid_coordinates(client, auth_token):
    """API rejects spot creation when coordinates are invalid."""
    # Arrange
    form_data = {
        "name": "Test Spot",
        "description": "Test description",
        "spot_type": "street",
        "difficulty": "beginner",
        "latitude": "not-a-number",
        "longitude": "also-not-a-number",
        "city": "Test City",
        "country": "Test Country",
        "is_public": "true",
    }

    # Act
    response = client.post(
        "/api/v1/skate-spots/",
        data=form_data,
        cookies={"access_token": auth_token},
    )

    # Assert
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "Invalid coordinates" in str(detail) or "coordinates" in str(detail).lower()


def test_create_spot_with_valid_coordinates(client, auth_token):
    """API accepts spot creation when valid coordinates are provided."""
    # Arrange
    form_data = {
        "name": "Valid Spot",
        "description": "Test description with valid location",
        "spot_type": "park",
        "difficulty": "intermediate",
        "latitude": "40.7128",
        "longitude": "-74.0060",
        "city": "New York",
        "country": "USA",
        "address": "123 Main St",
        "is_public": "true",
    }

    # Act
    response = client.post(
        "/api/v1/skate-spots/",
        data=form_data,
        cookies={"access_token": auth_token},
    )

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Valid Spot"
    assert data["location"]["latitude"] == 40.7128
    assert data["location"]["longitude"] == -74.0060
    assert data["location"]["city"] == "New York"
    assert data["location"]["country"] == "USA"
