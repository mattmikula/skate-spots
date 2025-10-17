# Tests 🧪

Comprehensive test suite for the Skate Spots Django application using pytest-django.

## Test Coverage

**102 tests** covering all functionality:

### Test Files

- **`conftest.py`** - Pytest fixtures for reusable test data
  - `client` - Django test client
  - `api_client` - DRF API client
  - `test_user` - Standard user fixture
  - `authenticated_api_client` - Authenticated API client
  - `admin_user` - Admin user fixture
  - `admin_api_client` - Authenticated admin API client
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

- **`test_ratings.py`** - Ratings API and models (14 tests)
  - Rating model creation and validation
  - String representation
  - Unique constraint (one rating per user per spot)
  - Cascade delete with spot
  - List and filter ratings by spot
  - Create rating (success, unauthenticated, duplicate, invalid score)
  - Update rating by owner/non-owner
  - Delete rating by owner/admin

- **`test_frontend_pages.py`** - HTML pages and forms (28 tests)
  - Page rendering (home, list, map, auth pages)
  - Form submissions (login, register, create/edit spots)
  - Authentication requirements
  - Owner-only access verification
  - Ratings UI tests: spot detail pages, rating display, form interactions

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
uv run pytest --cov=accounts --cov=spots --cov=ratings

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

### Example Rating Test

```python
@pytest.mark.django_db
def test_create_rating(authenticated_api_client, test_user):
    """Test creating a rating."""
    spot = SkateSpot.objects.create(
        name="Test Spot",
        description="Test",
        spot_type=SpotType.PARK,
        difficulty=Difficulty.BEGINNER,
        latitude=40.7128,
        longitude=-74.0060,
        city="NYC",
        country="USA",
        owner=test_user,
    )
    response = authenticated_api_client.post(
        "/api/v1/ratings/",
        {"spot": str(spot.id), "score": 5, "comment": "Excellent!"},
        format="json",
    )
    assert response.status_code == 201
    assert response.data["score"] == 5
    assert response.data["comment"] == "Excellent!"
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
