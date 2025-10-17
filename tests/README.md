# Tests

This directory is for Django tests using pytest-django.

## Setup

To add tests:

1. Install pytest-django:
```bash
pip install pytest-django
```

2. Create a `pytest.ini` file in the project root:
```ini
[pytest]
DJANGO_SETTINGS_MODULE = skate_spots_project.settings
python_files = tests.py test_*.py *_tests.py
```

3. Add tests in this directory following Django/pytest-django conventions.

## Example Test

```python
# tests/test_spots.py
import pytest
from django.contrib.auth import get_user_model
from spots.models import SkateSpot

User = get_user_model()

@pytest.mark.django_db
def test_create_spot():
    user = User.objects.create_user(username="test", email="test@test.com", password="test")
    spot = SkateSpot.objects.create(
        name="Test Spot",
        description="A test spot",
        spot_type="park",
        difficulty="beginner",
        latitude=40.7128,
        longitude=-74.0060,
        city="New York",
        country="USA",
        owner=user
    )
    assert spot.name == "Test Spot"
```

## Running Tests

```bash
make test
```
