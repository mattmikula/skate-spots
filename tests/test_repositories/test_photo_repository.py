"""Tests for the photo repository."""

from uuid import UUID, uuid4

import pytest
from sqlalchemy.orm import Session

from app.db.models import SkateSpotORM, UserORM
from app.models.photo import SpotPhotoCreate
from app.repositories.photo_repository import PhotoRepository


@pytest.fixture
def user(db_session: Session) -> UserORM:
    """Create a test user."""
    user = UserORM(
        id=str(uuid4()),
        email="test@example.com",
        username="testuser",
        hashed_password="hashedpassword",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def spot(db_session: Session, user: UserORM) -> SkateSpotORM:
    """Create a test skate spot."""
    spot = SkateSpotORM(
        id=str(uuid4()),
        name="Test Spot",
        description="A test skate spot",
        spot_type="park",
        difficulty="intermediate",
        latitude=40.7128,
        longitude=-74.0060,
        city="New York",
        country="USA",
        user_id=user.id,
    )
    db_session.add(spot)
    db_session.commit()
    db_session.refresh(spot)
    return spot


@pytest.fixture
def photo_repository(db_session: Session) -> PhotoRepository:
    """Create a photo repository with test session factory."""

    def session_factory():
        return db_session

    return PhotoRepository(session_factory=session_factory)


def test_create_photo(
    photo_repository: PhotoRepository,
    spot: SkateSpotORM,
    user: UserORM,
):
    """Test creating a new photo record."""
    photo_data = SpotPhotoCreate(caption="Great spot!", is_primary=True)

    photo = photo_repository.create(
        photo_data=photo_data,
        spot_id=UUID(spot.id),
        user_id=user.id,
        filename="test.jpg",
        file_path="2024-10/uuid/test.jpg",
    )

    assert photo.filename == "test.jpg"
    assert photo.file_path == "2024-10/uuid/test.jpg"
    assert photo.caption == "Great spot!"
    assert photo.is_primary is True
    assert photo.spot_id == UUID(spot.id)
    assert photo.user_id == user.id


def test_get_photo_by_id(
    photo_repository: PhotoRepository,
    spot: SkateSpotORM,
    user: UserORM,
):
    """Test retrieving a photo by ID."""
    photo_data = SpotPhotoCreate(caption="Test photo")
    created_photo = photo_repository.create(
        photo_data=photo_data,
        spot_id=UUID(spot.id),
        user_id=user.id,
        filename="test.jpg",
        file_path="2024-10/uuid/test.jpg",
    )

    retrieved_photo = photo_repository.get_by_id(created_photo.id)

    assert retrieved_photo is not None
    assert retrieved_photo.id == created_photo.id
    assert retrieved_photo.filename == "test.jpg"


def test_get_photo_by_id_not_found(photo_repository: PhotoRepository):
    """Test retrieving non-existent photo returns None."""
    photo = photo_repository.get_by_id(UUID("00000000-0000-0000-0000-000000000000"))
    assert photo is None


def test_get_photos_by_spot(
    photo_repository: PhotoRepository,
    spot: SkateSpotORM,
    user: UserORM,
):
    """Test retrieving all photos for a spot."""
    # Create multiple photos
    for i in range(3):
        photo_data = SpotPhotoCreate(caption=f"Photo {i}")
        photo_repository.create(
            photo_data=photo_data,
            spot_id=UUID(spot.id),
            user_id=user.id,
            filename=f"photo{i}.jpg",
            file_path=f"2024-10/uuid/photo{i}.jpg",
        )

    photos = photo_repository.get_by_spot(UUID(spot.id))

    assert len(photos) == 3
    # Should be ordered by creation date (descending - newest first)
    assert photos[0].filename == "photo2.jpg"
    assert photos[1].filename == "photo1.jpg"
    assert photos[2].filename == "photo0.jpg"


def test_get_photos_by_spot_empty(photo_repository: PhotoRepository):
    """Test retrieving photos for spot with no photos returns empty list."""
    spot_id = uuid4()
    photos = photo_repository.get_by_spot(spot_id)
    assert photos == []


def test_delete_photo(
    photo_repository: PhotoRepository,
    spot: SkateSpotORM,
    user: UserORM,
):
    """Test deleting a photo."""
    photo_data = SpotPhotoCreate()
    created_photo = photo_repository.create(
        photo_data=photo_data,
        spot_id=UUID(spot.id),
        user_id=user.id,
        filename="test.jpg",
        file_path="2024-10/uuid/test.jpg",
    )

    success = photo_repository.delete(created_photo.id)

    assert success is True
    assert photo_repository.get_by_id(created_photo.id) is None


def test_delete_photo_not_found(photo_repository: PhotoRepository):
    """Test deleting non-existent photo returns False."""
    success = photo_repository.delete(UUID("00000000-0000-0000-0000-000000000000"))
    assert success is False


def test_set_primary_photo(
    photo_repository: PhotoRepository,
    spot: SkateSpotORM,
    user: UserORM,
):
    """Test setting a photo as primary."""
    # Create two photos
    photo1_data = SpotPhotoCreate(is_primary=True)
    photo1 = photo_repository.create(
        photo_data=photo1_data,
        spot_id=UUID(spot.id),
        user_id=user.id,
        filename="photo1.jpg",
        file_path="2024-10/uuid/photo1.jpg",
    )

    photo2_data = SpotPhotoCreate(is_primary=False)
    photo2 = photo_repository.create(
        photo_data=photo2_data,
        spot_id=UUID(spot.id),
        user_id=user.id,
        filename="photo2.jpg",
        file_path="2024-10/uuid/photo2.jpg",
    )

    # Set photo2 as primary
    success = photo_repository.set_primary(photo2.id, UUID(spot.id))

    assert success is True
    # Verify photo2 is now primary
    updated_photo2 = photo_repository.get_by_id(photo2.id)
    assert updated_photo2.is_primary is True
    # Verify photo1 is no longer primary
    updated_photo1 = photo_repository.get_by_id(photo1.id)
    assert updated_photo1.is_primary is False


def test_set_primary_photo_not_found(
    photo_repository: PhotoRepository,
    spot: SkateSpotORM,
):
    """Test setting non-existent photo as primary returns False."""
    success = photo_repository.set_primary(
        UUID("00000000-0000-0000-0000-000000000000"),
        UUID(spot.id),
    )
    assert success is False


def test_get_primary_photo(
    photo_repository: PhotoRepository,
    spot: SkateSpotORM,
    user: UserORM,
):
    """Test retrieving the primary photo for a spot."""
    # Create multiple photos, only one is primary
    photo_repository.create(
        SpotPhotoCreate(is_primary=False),
        spot_id=UUID(spot.id),
        user_id=user.id,
        filename="photo1.jpg",
        file_path="2024-10/uuid/photo1.jpg",
    )

    primary_photo = photo_repository.create(
        SpotPhotoCreate(caption="Primary", is_primary=True),
        spot_id=UUID(spot.id),
        user_id=user.id,
        filename="primary.jpg",
        file_path="2024-10/uuid/primary.jpg",
    )

    photo_repository.create(
        SpotPhotoCreate(is_primary=False),
        spot_id=UUID(spot.id),
        user_id=user.id,
        filename="photo2.jpg",
        file_path="2024-10/uuid/photo2.jpg",
    )

    retrieved_primary = photo_repository.get_primary_by_spot(UUID(spot.id))

    assert retrieved_primary is not None
    assert retrieved_primary.id == primary_photo.id
    assert retrieved_primary.is_primary is True


def test_get_primary_photo_not_found(photo_repository: PhotoRepository):
    """Test retrieving primary photo when none exists returns None."""
    spot_id = uuid4()
    primary = photo_repository.get_primary_by_spot(spot_id)
    assert primary is None


def test_is_owner_true(
    photo_repository: PhotoRepository,
    spot: SkateSpotORM,
    user: UserORM,
):
    """Test checking ownership when user is the owner."""
    photo_data = SpotPhotoCreate()
    photo = photo_repository.create(
        photo_data=photo_data,
        spot_id=UUID(spot.id),
        user_id=user.id,
        filename="test.jpg",
        file_path="2024-10/uuid/test.jpg",
    )

    is_owner = photo_repository.is_owner(photo.id, user.id)

    assert is_owner is True


def test_is_owner_false(
    photo_repository: PhotoRepository,
    spot: SkateSpotORM,
    user: UserORM,
):
    """Test checking ownership when user is not the owner."""
    photo_data = SpotPhotoCreate()
    photo = photo_repository.create(
        photo_data=photo_data,
        spot_id=UUID(spot.id),
        user_id=user.id,
        filename="test.jpg",
        file_path="2024-10/uuid/test.jpg",
    )

    other_user_id = str(uuid4())
    is_owner = photo_repository.is_owner(photo.id, other_user_id)

    assert is_owner is False


def test_is_owner_photo_not_found(photo_repository: PhotoRepository):
    """Test checking ownership for non-existent photo returns False."""
    is_owner = photo_repository.is_owner(
        UUID("00000000-0000-0000-0000-000000000000"),
        "some-user-id",
    )
    assert is_owner is False
