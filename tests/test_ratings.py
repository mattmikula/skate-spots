"""Tests for ratings functionality."""

import pytest
from django.contrib.auth import get_user_model
from ratings.models import Rating
from spots.models import Difficulty, SkateSpot, SpotType

User = get_user_model()


class TestRatingModel:
    """Tests for Rating model."""

    @pytest.mark.django_db
    def test_create_rating(self, test_user):
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
        rating = Rating.objects.create(
            spot=spot, user=test_user, score=5, comment="Great spot!"
        )
        assert rating.score == 5
        assert rating.comment == "Great spot!"
        assert rating.user == test_user
        assert rating.spot == spot

    @pytest.mark.django_db
    def test_rating_string_representation(self, test_user):
        """Test rating string representation."""
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
        rating = Rating.objects.create(spot=spot, user=test_user, score=4)
        assert str(rating) == f"{test_user.username} rated Test Spot: 4/5"

    @pytest.mark.django_db
    def test_rating_unique_constraint(self, test_user):
        """Test that a user can only rate a spot once."""
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
        Rating.objects.create(spot=spot, user=test_user, score=5)

        # Try to create duplicate rating
        with pytest.raises(Exception):
            Rating.objects.create(spot=spot, user=test_user, score=3)

    @pytest.mark.django_db
    def test_rating_cascade_delete_with_spot(self, test_user):
        """Test that ratings are deleted when spot is deleted."""
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
        rating = Rating.objects.create(spot=spot, user=test_user, score=5)
        rating_id = rating.id

        spot.delete()
        assert not Rating.objects.filter(id=rating_id).exists()


class TestRatingAPI:
    """Tests for Rating API endpoints."""

    @pytest.mark.django_db
    def test_list_ratings(self, api_client, test_user):
        """Test listing all ratings."""
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
        Rating.objects.create(spot=spot, user=test_user, score=5)

        response = api_client.get("/api/v1/ratings/")
        assert response.status_code == 200
        assert len(response.data) == 1

    @pytest.mark.django_db
    def test_filter_ratings_by_spot(self, api_client, test_user, another_user):
        """Test filtering ratings by spot."""
        spot1 = SkateSpot.objects.create(
            name="Spot 1",
            description="Test",
            spot_type=SpotType.PARK,
            difficulty=Difficulty.BEGINNER,
            latitude=40.7128,
            longitude=-74.0060,
            city="NYC",
            country="USA",
            owner=test_user,
        )
        spot2 = SkateSpot.objects.create(
            name="Spot 2",
            description="Test",
            spot_type=SpotType.STREET,
            difficulty=Difficulty.ADVANCED,
            latitude=34.0522,
            longitude=-118.2437,
            city="LA",
            country="USA",
            owner=test_user,
        )
        Rating.objects.create(spot=spot1, user=test_user, score=5)
        Rating.objects.create(spot=spot2, user=another_user, score=3)

        response = api_client.get(f"/api/v1/ratings/?spot={spot1.id}")
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["spot_name"] == "Spot 1"

    @pytest.mark.django_db
    def test_create_rating_success(self, authenticated_api_client, test_user):
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
        assert Rating.objects.count() == 1

    @pytest.mark.django_db
    def test_create_rating_unauthenticated(self, api_client, test_user):
        """Test creating rating without authentication fails."""
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
        response = api_client.post(
            "/api/v1/ratings/",
            {"spot": str(spot.id), "score": 5},
            format="json",
        )
        assert response.status_code == 401

    @pytest.mark.django_db
    def test_create_duplicate_rating_fails(self, authenticated_api_client, test_user):
        """Test that creating duplicate rating for same spot fails."""
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
        # Create first rating
        authenticated_api_client.post(
            "/api/v1/ratings/",
            {"spot": str(spot.id), "score": 5},
            format="json",
        )

        # Try to create second rating
        response = authenticated_api_client.post(
            "/api/v1/ratings/",
            {"spot": str(spot.id), "score": 3},
            format="json",
        )
        assert response.status_code == 400
        assert "already rated" in response.data["detail"]

    @pytest.mark.django_db
    def test_create_rating_invalid_score(self, authenticated_api_client, test_user):
        """Test creating rating with invalid score fails."""
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
            {"spot": str(spot.id), "score": 6},  # Invalid: max is 5
            format="json",
        )
        assert response.status_code == 400

    @pytest.mark.django_db
    def test_update_rating_by_owner(self, authenticated_api_client, test_user):
        """Test updating a rating as the owner."""
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
        rating = Rating.objects.create(
            spot=spot, user=test_user, score=3, comment="Okay"
        )

        response = authenticated_api_client.patch(
            f"/api/v1/ratings/{rating.id}/",
            {"score": 5, "comment": "Actually great!"},
            format="json",
        )
        assert response.status_code == 200
        assert response.data["score"] == 5
        assert response.data["comment"] == "Actually great!"

    @pytest.mark.django_db
    def test_update_rating_by_non_owner(self, api_client, test_user, another_user):
        """Test updating rating as non-owner fails."""
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
        rating = Rating.objects.create(spot=spot, user=test_user, score=5)

        api_client.force_authenticate(user=another_user)
        response = api_client.patch(
            f"/api/v1/ratings/{rating.id}/", {"score": 1}, format="json"
        )
        assert response.status_code == 403

    @pytest.mark.django_db
    def test_delete_rating_by_owner(self, authenticated_api_client, test_user):
        """Test deleting rating as the owner."""
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
        rating = Rating.objects.create(spot=spot, user=test_user, score=5)

        response = authenticated_api_client.delete(f"/api/v1/ratings/{rating.id}/")
        assert response.status_code == 204
        assert not Rating.objects.filter(id=rating.id).exists()

    @pytest.mark.django_db
    def test_delete_rating_by_admin(self, admin_api_client, test_user):
        """Test deleting rating as admin."""
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
        rating = Rating.objects.create(spot=spot, user=test_user, score=5)

        response = admin_api_client.delete(f"/api/v1/ratings/{rating.id}/")
        assert response.status_code == 204
        assert not Rating.objects.filter(id=rating.id).exists()
