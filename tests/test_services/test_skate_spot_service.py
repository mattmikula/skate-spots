"""Tests for skate spot services."""

from uuid import uuid4

import pytest

from app.models.skate_spot import (
    Difficulty,
    Location,
    SkateSpotCreate,
    SkateSpotFilters,
    SkateSpotUpdate,
    SpotType,
)
from app.repositories.skate_spot_repository import SkateSpotRepository
from app.services.skate_spot_service import SkateSpotService


# Repository tests
@pytest.fixture
def repository(session_factory):
    """Create a repository backed by the in-memory test database."""

    return SkateSpotRepository(session_factory=session_factory)


@pytest.fixture
def sample_spot_data():
    """Sample skate spot data for testing."""

    return SkateSpotCreate(
        name="Test Spot",
        description="A great test spot",
        spot_type=SpotType.RAIL,
        difficulty=Difficulty.INTERMEDIATE,
        location=Location(
            latitude=40.7128,
            longitude=-74.0060,
            city="New York",
            country="USA",
        ),
        is_public=True,
        requires_permission=False,
    )


@pytest.fixture
def created_spot(repository, sample_spot_data):
    """Create a spot in repository and return it."""

    return repository.create(sample_spot_data, user_id="test-user-id")


@pytest.fixture
def second_spot(repository, sample_spot_data):
    """Create a second spot in repository and return it."""

    modified = sample_spot_data.model_copy(update={"name": "Second Spot"})
    return repository.create(modified, user_id="test-user-id")


@pytest.fixture
def deleted_spot_id(repository, sample_spot_data):
    """Create a spot, delete it, and return its ID."""

    spot = repository.create(sample_spot_data, user_id="test-user-id")
    repository.delete(spot.id)
    return spot.id


# Repository create tests
def test_create_spot(repository, sample_spot_data):
    """Test creating a new spot."""

    spot = repository.create(sample_spot_data, user_id="test-user-id")

    assert spot.name == "Test Spot"
    assert spot.spot_type == SpotType.RAIL
    assert spot.id is not None
    assert spot.created_at is not None
    assert spot.average_rating is None
    assert spot.ratings_count == 0


# Repository read tests
def test_get_by_id_existing(repository, created_spot):
    """Test getting an existing spot by ID."""

    retrieved_spot = repository.get_by_id(created_spot.id)

    assert retrieved_spot is not None
    assert retrieved_spot.id == created_spot.id
    assert retrieved_spot.name == created_spot.name
    assert retrieved_spot.average_rating is None
    assert retrieved_spot.ratings_count == 0


def test_get_by_id_nonexistent(repository):
    """Test getting a non-existent spot by ID."""

    non_existent_id = uuid4()
    spot = repository.get_by_id(non_existent_id)
    assert spot is None


def test_get_all_empty(repository):
    """Test getting all spots from empty repository."""

    spots = repository.get_all()
    assert spots == []


def test_get_all_with_spots(repository, created_spot, second_spot):
    """Test getting all spots when spots exist."""

    all_spots = repository.get_all()
    assert len(all_spots) == 2
    assert created_spot in all_spots
    assert second_spot in all_spots


def test_get_all_with_filters(repository, sample_spot_data):
    """Repository returns only spots that match provided filters."""

    repository.create(sample_spot_data, user_id="test-user-id")

    advanced_location = Location(
        latitude=34.0522,
        longitude=-118.2437,
        city="Los Angeles",
        country="USA",
    )
    advanced_data = sample_spot_data.model_copy(
        update={
            "name": "Advanced Bowl",
            "description": "Deep bowl requiring permission",
            "spot_type": SpotType.BOWL,
            "difficulty": Difficulty.ADVANCED,
            "location": advanced_location,
            "is_public": False,
            "requires_permission": True,
        }
    )
    repository.create(advanced_data, user_id="test-user-id")

    filters = SkateSpotFilters(
        difficulties=[Difficulty.ADVANCED],
        spot_types=[SpotType.BOWL],
        city="los angeles",
        is_public=False,
        requires_permission=True,
    )

    filtered_spots = repository.get_all(filters)

    assert len(filtered_spots) == 1
    assert filtered_spots[0].name == "Advanced Bowl"

    search_filters = SkateSpotFilters(search="los")
    search_results = repository.get_all(search_filters)

    assert len(search_results) == 1
    assert search_results[0].name == "Advanced Bowl"


# Repository update tests
def test_update_existing_spot(repository, created_spot):
    """Test updating an existing spot."""

    update_data = SkateSpotUpdate(
        name="Updated Name",
        difficulty=Difficulty.ADVANCED,
    )

    updated_spot = repository.update(created_spot.id, update_data)

    assert updated_spot is not None
    assert updated_spot.name == "Updated Name"
    assert updated_spot.difficulty == Difficulty.ADVANCED
    assert updated_spot.description == created_spot.description
    assert updated_spot.updated_at >= created_spot.updated_at


def test_update_nonexistent_spot(repository):
    """Test updating a non-existent spot."""

    non_existent_id = uuid4()
    update_data = SkateSpotUpdate(name="Updated Name")

    updated_spot = repository.update(non_existent_id, update_data)
    assert updated_spot is None


# Repository delete tests
def test_delete_existing_spot(repository, created_spot):
    """Test deleting an existing spot."""

    success = repository.delete(created_spot.id)
    assert success is True


def test_get_deleted_spot_returns_none(repository, deleted_spot_id):
    """Test that getting a deleted spot returns None."""

    deleted_spot = repository.get_by_id(deleted_spot_id)
    assert deleted_spot is None


def test_delete_nonexistent_spot(repository):
    """Test deleting a non-existent spot."""

    non_existent_id = uuid4()
    success = repository.delete(non_existent_id)
    assert success is False


# Service layer tests
@pytest.fixture
def service(session_factory):
    """Create a fresh service for each test."""

    repository = SkateSpotRepository(session_factory=session_factory)
    return SkateSpotService(repository)


@pytest.fixture
def service_spot_data():
    """Sample skate spot data for service testing."""

    return SkateSpotCreate(
        name="Service Test Spot",
        description="A spot for testing the service",
        spot_type=SpotType.PARK,
        difficulty=Difficulty.BEGINNER,
        location=Location(
            latitude=37.7749,
            longitude=-122.4194,
            city="San Francisco",
            country="USA",
        ),
    )


@pytest.fixture
def created_service_spot(service, service_spot_data):
    """Create a spot through service and return it."""

    return service.create_spot(service_spot_data, user_id="test-user-id")


@pytest.fixture
def second_service_spot(service, service_spot_data):
    """Create a second spot through service and return it."""

    modified = service_spot_data.model_copy(update={"name": "Second Service Spot"})
    return service.create_spot(modified, user_id="test-user-id")


@pytest.fixture
def deleted_service_spot_id(service, service_spot_data):
    """Create a spot through service, delete it, and return its ID."""

    spot = service.create_spot(service_spot_data, user_id="test-user-id")
    service.delete_spot(spot.id)
    return spot.id


# Service create tests
def test_service_create_spot(service, service_spot_data):
    """Test creating a spot through service."""

    spot = service.create_spot(service_spot_data, user_id="test-user-id")

    assert spot.name == "Service Test Spot"
    assert spot.spot_type == SpotType.PARK
    assert spot.id is not None


# Service read tests
def test_service_get_spot(service, created_service_spot):
    """Test getting a spot through service."""

    retrieved_spot = service.get_spot(created_service_spot.id)

    assert retrieved_spot is not None
    assert retrieved_spot.id == created_service_spot.id


def test_service_get_nonexistent_spot(service):
    """Test getting a non-existent spot through service."""

    non_existent_id = uuid4()
    spot = service.get_spot(non_existent_id)
    assert spot is None


def test_service_list_empty_spots(service):
    """Test listing spots when service is empty."""

    spots = service.list_spots()
    assert len(spots) == 0


def test_service_list_spots_with_data(service, created_service_spot, second_service_spot):
    """Test listing spots when spots exist."""

    spots = service.list_spots()
    assert len(spots) == 2
    spot_ids = [spot.id for spot in spots]
    assert created_service_spot.id in spot_ids
    assert second_service_spot.id in spot_ids


def test_service_list_spots_with_filters(service, service_spot_data):
    """Service honours filters when listing spots."""

    service.create_spot(service_spot_data, user_id="test-user-id")

    advanced_location = Location(
        latitude=34.0522,
        longitude=-118.2437,
        city="Los Angeles",
        country="USA",
    )
    advanced_data = service_spot_data.model_copy(
        update={
            "name": "Advanced Bowl",
            "description": "Deep bowl requiring permission",
            "spot_type": SpotType.BOWL,
            "difficulty": Difficulty.ADVANCED,
            "location": advanced_location,
            "is_public": False,
            "requires_permission": True,
        }
    )
    created = service.create_spot(advanced_data, user_id="test-user-id")

    filters = SkateSpotFilters(search="bowl", is_public=False)
    spots = service.list_spots(filters)

    assert len(spots) == 1
    assert spots[0].id == created.id


# Service update tests
def test_service_update_spot(service, created_service_spot):
    """Test updating a spot through service."""

    update_data = SkateSpotUpdate(
        name="Updated Service Spot",
        spot_type=SpotType.BOWL,
    )

    updated_spot = service.update_spot(created_service_spot.id, update_data)

    assert updated_spot is not None
    assert updated_spot.name == "Updated Service Spot"
    assert updated_spot.spot_type == SpotType.BOWL


def test_service_update_nonexistent_spot(service):
    """Test updating a non-existent spot through service."""

    non_existent_id = uuid4()
    update_data = SkateSpotUpdate(name="Won't work")

    updated_spot = service.update_spot(non_existent_id, update_data)
    assert updated_spot is None


# Service delete tests
def test_service_delete_spot(service, created_service_spot):
    """Test deleting a spot through service."""

    success = service.delete_spot(created_service_spot.id)
    assert success is True


def test_service_get_deleted_spot_through_service(service, deleted_service_spot_id):
    """Test that getting a deleted spot through service returns None."""

    deleted_spot = service.get_spot(deleted_service_spot_id)
    assert deleted_spot is None


def test_service_delete_nonexistent_spot(service):
    """Test deleting a non-existent spot through service."""

    non_existent_id = uuid4()
    success = service.delete_spot(non_existent_id)
    assert success is False


def test_service_repository_shared_database(session_factory):
    """Different services using the same factory should see shared data."""

    repo1 = SkateSpotRepository(session_factory=session_factory)
    repo2 = SkateSpotRepository(session_factory=session_factory)
    service1 = SkateSpotService(repo1)
    service2 = SkateSpotService(repo2)

    spot_data = SkateSpotCreate(
        name="Shared Spot",
        description="Testing shared persistence",
        spot_type=SpotType.STREET,
        difficulty=Difficulty.EXPERT,
        location=Location(
            latitude=0.0,
            longitude=0.0,
            city="Test City",
            country="Test Country",
        ),
    )

    created = service1.create_spot(spot_data, user_id="test-user-id")

    assert service1.get_spot(created.id) is not None
    assert service2.get_spot(created.id) is not None
    assert len(service2.list_spots()) == 1
