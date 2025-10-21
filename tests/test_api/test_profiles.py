from datetime import datetime, timedelta
from uuid import uuid4

from app.db.models import (
    RatingORM,
    SessionORM,
    SessionRSVPORM,
    SkateSpotORM,
    SpotCommentORM,
    SpotPhotoORM,
)
from app.models.user import UserCreate
from app.repositories.user_repository import UserRepository


def _seed_profile(session_factory):
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
        user.bio = "Spot hunter and filmer."
        user.location = "Barcelona, ES"
        session.commit()

        base_time = datetime.utcnow() - timedelta(days=1)
        spot = SkateSpotORM(
            id=str(uuid4()),
            name="Raval Plaza",
            description="Perfect for lines",
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
            content="Legendary manual pads.",
            created_at=base_time + timedelta(hours=1),
            updated_at=base_time + timedelta(hours=1),
        )
        session.add(comment)

        rating = RatingORM(
            id=str(uuid4()),
            spot_id=spot.id,
            user_id=str(user.id),
            score=5,
            comment="Dream spot",
            created_at=base_time + timedelta(hours=2),
            updated_at=base_time + timedelta(hours=2),
        )
        session.add(rating)

        photo = SpotPhotoORM(
            id=str(uuid4()),
            spot_id=spot.id,
            uploader_id=str(user.id),
            file_path="media/test.jpg",
            created_at=base_time + timedelta(hours=3),
        )
        session.add(photo)

        hosted_session = SessionORM(
            id=str(uuid4()),
            spot_id=spot.id,
            organizer_id=str(user.id),
            title="Evening Lines",
            description="Work on manuals",
            start_time=base_time + timedelta(hours=4),
            end_time=base_time + timedelta(hours=5),
            meet_location="Central ledge",
            skill_level="Intermediate",
            capacity=6,
            status="scheduled",
            created_at=base_time + timedelta(hours=4),
            updated_at=base_time + timedelta(hours=4),
        )
        session.add(hosted_session)

        rsvp = SessionRSVPORM(
            id=str(uuid4()),
            session_id=hosted_session.id,
            user_id=str(user.id),
            response="going",
            created_at=base_time + timedelta(hours=4, minutes=15),
            updated_at=base_time + timedelta(hours=4, minutes=15),
        )
        session.add(rsvp)

        session.commit()
        return user.username


def test_public_profile_page_renders(client, session_factory):
    username = _seed_profile(session_factory)

    response = client.get(f"/users/{username}")

    assert response.status_code == 200
    assert "Profile User" in response.text
    assert "Spots created" in response.text
    assert "Recent activity" in response.text


def test_public_profile_page_missing_user_returns_404(client):
    response = client.get("/users/unknown-user")
    assert response.status_code == 404
    assert "Skater not found" in response.text
