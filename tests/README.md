# Tests 🧪

Comprehensive test suite for the Skate Spots Django application using pytest-django.

## Test Coverage

**81 tests** covering all functionality:

### Test Files

- **`conftest.py`** - Pytest fixtures for reusable test data
  - `client` - Django test client
  - `api_client` - DRF API client
  - `test_user` - Standard user fixture
  - `authenticated_api_client` - Authenticated API client
  - `admin_user` - Admin user fixture
  - `another_user` - Second user for permission tests

- **`test_models.py`** - Model validation and behavior (12 tests)
  - User model creation and uniqueness
  - SkateSpot model validation
  - Location constraints (lat/lon ranges)
  - Cascade delete behavior
  - All spot types and difficulties

- **`test_api_endpoints.py`** - REST API endpoints (33 tests)
  - Authentication flow (register, login, logout, me)
  - CRUD operations (create, read, update, delete)
  - Filtering by city, difficulty, type
  - GeoJSON endpoint
  - Permission checks (owner/admin)

- **`test_frontend_pages.py`** - HTML pages and forms (21 tests)
  - Page rendering (home, list, map, auth pages)
  - Form submissions (login, register, create/edit spots)
  - Authentication requirements
  - Owner-only access verification

- **`test_rate_limiting.py`** - Security and rate limits (15 tests)
  - Rate limiting decorator configuration
  - Write operation protection
  - Read operation accessibility
  - Authentication enforcement

## Running Tests

```bash
# Run all tests
make test

# Run specific test file
uv run pytest tests/test_models.py

# Run with verbose output
uv run pytest -v

# Run with coverage
uv run pytest --cov=accounts --cov=spots

# Run linting and tests
make check
```

## Writing New Tests

### Example Model Test

```python
import pytest
from django.contrib.auth import get_user_model
from spots.models import SkateSpot, SpotType, Difficulty

User = get_user_model()

@pytest.mark.django_db
def test_spot_creation(test_user):
    """Test creating a skate spot."""
    spot = SkateSpot.objects.create(
        name="Test Spot",
        description="A great spot",
        spot_type=SpotType.PARK,
        difficulty=Difficulty.INTERMEDIATE,
        latitude=40.7128,
        longitude=-74.0060,
        city="New York",
        country="USA",
        owner=test_user
    )
    assert spot.name == "Test Spot"
    assert spot.owner == test_user
```

### Example API Test

```python
@pytest.mark.django_db
def test_create_spot_api(authenticated_api_client):
    """Test creating spot via API."""
    response = authenticated_api_client.post(
        "/api/v1/skate-spots/",
        {
            "name": "New Spot",
            "description": "Test",
            "spot_type": "park",
            "difficulty": "beginner",
            "location": {
                "latitude": 40.7128,
                "longitude": -74.0060,
                "city": "NYC",
                "country": "USA"
            },
            "is_public": True,
            "requires_permission": False
        },
        format="json"
    )
    assert response.status_code == 201
    assert response.data["name"] == "New Spot"
```

## Test Configuration

Configured in `pytest.ini`:
```ini
[pytest]
DJANGO_SETTINGS_MODULE = skate_spots_project.settings
python_files = tests.py test_*.py *_tests.py
testpaths = tests
```

## CI/CD Integration

Tests run automatically on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`

See `.github/workflows/ci.yml` for CI configuration.
