"""Tests for models."""

import pytest
from django.contrib.auth import get_user_model
from spots.models import Difficulty, SkateSpot, SpotType

User = get_user_model()


class TestUserModel:
    """Tests for User model."""

    @pytest.mark.django_db
    def test_create_user(self):
        """Test creating a user."""
        user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass"
        )
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.check_password("testpass")
        assert not user.is_admin

    @pytest.mark.django_db
    def test_user_unique_email(self):
        """Test that email must be unique."""
        User.objects.create_user(
            email="test@example.com",
            username="user1",
            password="pass1"
        )
        with pytest.raises(Exception):  # IntegrityError
            User.objects.create_user(
                email="test@example.com",
                username="user2",
                password="pass2"
            )

    @pytest.mark.django_db
    def test_user_unique_username(self):
        """Test that username must be unique."""
        User.objects.create_user(
            email="user1@example.com",
            username="testuser",
            password="pass1"
        )
        with pytest.raises(Exception):  # IntegrityError
            User.objects.create_user(
                email="user2@example.com",
                username="testuser",
                password="pass2"
            )

    @pytest.mark.django_db
    def test_user_is_active_by_default(self):
        """Test that users are active by default."""
        user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass"
        )
        assert user.is_active


class TestSkateSpotModel:
    """Tests for SkateSpot model."""

    @pytest.mark.django_db
    def test_create_skate_spot(self, test_user):
        """Test creating a skate spot."""
        spot = SkateSpot.objects.create(
            name="Test Spot",
            description="A test spot",
            spot_type=SpotType.PARK,
            difficulty=Difficulty.BEGINNER,
            latitude=40.7128,
            longitude=-74.0060,
            city="New York",
            country="USA",
            owner=test_user
        )
        assert spot.name == "Test Spot"
        assert spot.spot_type == SpotType.PARK
        assert spot.difficulty == Difficulty.BEGINNER
        assert spot.owner == test_user

    @pytest.mark.django_db
    def test_spot_string_representation(self, test_user):
        """Test spot string representation."""
        spot = SkateSpot.objects.create(
            name="Downtown Rails",
            description="Great spot",
            spot_type=SpotType.RAIL,
            difficulty=Difficulty.INTERMEDIATE,
            latitude=40.7128,
            longitude=-74.0060,
            city="New York",
            country="USA",
            owner=test_user
        )
        assert str(spot) == "Downtown Rails (New York, USA)"

    @pytest.mark.django_db
    def test_spot_optional_address(self, test_user):
        """Test that address is optional."""
        spot = SkateSpot.objects.create(
            name="Test Spot",
            description="A test spot",
            spot_type=SpotType.STREET,
            difficulty=Difficulty.ADVANCED,
            latitude=40.7128,
            longitude=-74.0060,
            city="New York",
            country="USA",
            owner=test_user
        )
        assert spot.address is None

    @pytest.mark.django_db
    def test_spot_with_address(self, test_user):
        """Test spot with address."""
        spot = SkateSpot.objects.create(
            name="Test Spot",
            description="A test spot",
            spot_type=SpotType.STREET,
            difficulty=Difficulty.ADVANCED,
            latitude=40.7128,
            longitude=-74.0060,
            address="123 Main St",
            city="New York",
            country="USA",
            owner=test_user
        )
        assert spot.address == "123 Main St"

    @pytest.mark.django_db
    def test_spot_defaults(self, test_user):
        """Test spot default values."""
        spot = SkateSpot.objects.create(
            name="Test Spot",
            description="A test spot",
            spot_type=SpotType.PARK,
            difficulty=Difficulty.BEGINNER,
            latitude=40.7128,
            longitude=-74.0060,
            city="New York",
            country="USA",
            owner=test_user
        )
        assert spot.is_public is True
        assert spot.requires_permission is False

    @pytest.mark.django_db
    def test_spot_all_types(self, test_user):
        """Test all spot types."""
        for spot_type in SpotType:
            spot = SkateSpot.objects.create(
                name=f"Test {spot_type.label}",
                description="A test spot",
                spot_type=spot_type,
                difficulty=Difficulty.BEGINNER,
                latitude=40.7128,
                longitude=-74.0060,
                city="New York",
                country="USA",
                owner=test_user
            )
            assert spot.spot_type == spot_type

    @pytest.mark.django_db
    def test_spot_all_difficulties(self, test_user):
        """Test all difficulty levels."""
        for difficulty in Difficulty:
            spot = SkateSpot.objects.create(
                name=f"Test {difficulty.label}",
                description="A test spot",
                spot_type=SpotType.PARK,
                difficulty=difficulty,
                latitude=40.7128,
                longitude=-74.0060,
                city="New York",
                country="USA",
                owner=test_user
            )
            assert spot.difficulty == difficulty

    @pytest.mark.django_db
    def test_spot_latitude_validation(self, test_user):
        """Test latitude validation."""
        # Invalid latitude > 90
        with pytest.raises(Exception):  # ValidationError
            spot = SkateSpot.objects.create(
                name="Test",
                description="Test",
                spot_type=SpotType.PARK,
                difficulty=Difficulty.BEGINNER,
                latitude=91,
                longitude=-74.0060,
                city="New York",
                country="USA",
                owner=test_user
            )
            spot.full_clean()

    @pytest.mark.django_db
    def test_spot_longitude_validation(self, test_user):
        """Test longitude validation."""
        # Invalid longitude > 180
        with pytest.raises(Exception):  # ValidationError
            spot = SkateSpot.objects.create(
                name="Test",
                description="Test",
                spot_type=SpotType.PARK,
                difficulty=Difficulty.BEGINNER,
                latitude=40.7128,
                longitude=181,
                city="New York",
                country="USA",
                owner=test_user
            )
            spot.full_clean()

    @pytest.mark.django_db
    def test_spot_cascade_delete(self):
        """Test that deleting user deletes their spots."""
        user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass"
        )
        spot = SkateSpot.objects.create(
            name="Test Spot",
            description="A test spot",
            spot_type=SpotType.PARK,
            difficulty=Difficulty.BEGINNER,
            latitude=40.7128,
            longitude=-74.0060,
            city="New York",
            country="USA",
            owner=user
        )
        spot_id = spot.id
        user.delete()
        assert not SkateSpot.objects.filter(id=spot_id).exists()
