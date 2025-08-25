"""Shared test fixtures and configuration."""

import pytest
from fastapi.testclient import TestClient

from app.services.skate_spot_service import SkateSpotRepository, SkateSpotService
from main import app


@pytest.fixture(scope="session")
def test_client():
    """Create a test client that persists for the entire test session."""
    with TestClient(app) as client:
        yield client


@pytest.fixture(autouse=True)
def clean_global_repository():
    """Clean the global repository before each test to ensure isolation."""
    # Import the global service and clear its repository
    from app.services.skate_spot_service import _repository

    _repository._spots.clear()
    yield
    # Clean up after test as well
    _repository._spots.clear()


@pytest.fixture
def fresh_service():
    """Create a fresh service with isolated repository for testing."""
    repository = SkateSpotRepository()
    service = SkateSpotService(repository)
    return service
