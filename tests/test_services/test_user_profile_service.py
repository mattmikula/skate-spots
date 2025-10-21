from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from app.db.models import RatingORM, SkateSpotORM, SpotCommentORM, SpotPhotoORM
from app.models.user import UserCreate
from app.repositories.user_profile_repository import UserProfileRepository
from app.repositories.user_repository import UserRepository
from app.services.user_profile_service import (
    UserProfileNotFoundError,
    UserProfileService,
)


def _seed_user_with_activity(session_factory):
    with session_factory() as session:
        repo = UserRepository(session)
        user = repo.create(
            UserCreate(
                email="profile@example.com",
                username="profile-user",
                password="changeme123",
            ),
            hashed_password="hashed",
        )
        user.display_name = "Profile User"
        user.bio = "Loves skating ledges and bowls."
        user.location = "Barcelona, ES"
        user.website_url = "https://example.com"
        user.instagram_handle = "@sk8profile"
        session.commit()

        base_time = datetime.utcnow() - timedelta(days=1)
        spot = SkateSpotORM(
            id=str(uuid4()),
            name="Test Spot",
            description="Smooth ground with rails",
            spot_type="street",
            difficulty="intermediate",
            latitude=41.0,
            longitude=2.0,
            address="123 Skate St",
            city="Barcelona",
            country="Spain",
            is_public=True,
            requires_permission=False,
            user_id=str(user.id),
            created_at=base_time,
            updated_at=base_time,
        )
        session.add(spot)

        comment = SpotCommentORM(
            id=str(uuid4()),
            spot_id=spot.id,
            user_id=str(user.id),
            content="Great ledges for manuals!",
            created_at=base_time + timedelta(hours=2),
            updated_at=base_time + timedelta(hours=2),
        )
        session.add(comment)

        rating = RatingORM(
            id=str(uuid4()),
            spot_id=spot.id,
            user_id=str(user.id),
            score=4,
            comment="Flowy lines",
            created_at=base_time + timedelta(hours=3),
            updated_at=base_time + timedelta(hours=3),
        )
        session.add(rating)

        photo = SpotPhotoORM(
            id=str(uuid4()),
            spot_id=spot.id,
            uploader_id=str(user.id),
            file_path="media/test.jpg",
            original_filename="test.jpg",
            created_at=base_time + timedelta(hours=1),
        )
        session.add(photo)

        session.commit()
        return str(user.username)


def test_get_profile_returns_activity(session_factory):
    username = _seed_user_with_activity(session_factory)

    repository = UserProfileRepository(session_factory=session_factory)
    service = UserProfileService(repository)

    profile = service.get_profile(username)

    assert profile.username == "profile-user"
    assert profile.display_name == "Profile User"
    assert profile.stats.spots_added == 1
    assert profile.stats.photos_uploaded == 1
    assert profile.stats.comments_posted == 1
    assert profile.stats.ratings_left == 1
    assert any(item.type.value == "spot_created" for item in profile.activity)


def test_get_profile_missing_user_raises(session_factory):
    repository = UserProfileRepository(session_factory=session_factory)
    service = UserProfileService(repository)

    with pytest.raises(UserProfileNotFoundError):
        service.get_profile("does-not-exist")
