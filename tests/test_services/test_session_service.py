from datetime import datetime, timedelta

import pytest

from app.models.session import SessionCreate, SessionResponse, SessionRSVPCreate
from app.models.skate_spot import Difficulty, Location, SkateSpotCreate, SpotType
from app.models.user import UserCreate
from app.repositories.session_repository import SessionRepository
from app.repositories.skate_spot_repository import SkateSpotRepository
from app.repositories.user_repository import UserRepository
from app.services.session_service import SessionCapacityError, SessionService


def _create_user(session_factory, email: str, username: str):
    with session_factory() as db:
        repo = UserRepository(db)
        user = repo.create(
            UserCreate(email=email, username=username, password="changeme123"),
            hashed_password="hashed",
        )
        db.expunge(user)
        return user


def _create_spot(session_factory, owner_id: str):
    spot_repo = SkateSpotRepository(session_factory=session_factory)
    return spot_repo.create(
        SkateSpotCreate(
            name="Community Park",
            description="Smooth lines for everyone",
            spot_type=SpotType.PARK,
            difficulty=Difficulty.BEGINNER,
            location=Location(
                latitude=40.0,
                longitude=-74.0,
                city="Test City",
                country="Testland",
            ),
            photos=[],
        ),
        owner_id,
    )


def _service(session_factory) -> SessionService:
    return SessionService(
        SessionRepository(session_factory=session_factory),
        SkateSpotRepository(session_factory=session_factory),
    )


def test_create_and_list_session(session_factory):
    service = _service(session_factory)
    organizer = _create_user(session_factory, "organizer@example.com", "organizer")
    spot = _create_spot(session_factory, organizer.id)

    payload = SessionCreate(
        title="Sunrise Flow",
        description="Warm-up laps",
        start_time=datetime.utcnow() + timedelta(hours=2),
        end_time=datetime.utcnow() + timedelta(hours=3),
        meet_location="Main gate",
        skill_level="Beginner",
        capacity=6,
    )

    session = service.create_session(spot.id, organizer, payload)
    assert session.title == "Sunrise Flow"
    listed = service.list_upcoming_sessions(spot.id, current_user_id=str(organizer.id))
    assert len(listed) == 1
    assert listed[0].stats.going == 0
    assert listed[0].user_response is None


def test_waitlist_promotion_after_withdraw(session_factory):
    service = _service(session_factory)
    organizer = _create_user(session_factory, "organizer@example.com", "organizer")
    attendee = _create_user(session_factory, "attendee@example.com", "attendee")
    spot = _create_spot(session_factory, organizer.id)

    payload = SessionCreate(
        title="Capacity Test",
        description="",
        start_time=datetime.utcnow() + timedelta(hours=1),
        end_time=datetime.utcnow() + timedelta(hours=2),
        capacity=1,
    )
    session = service.create_session(spot.id, organizer, payload)

    service.rsvp_session(session.id, organizer, SessionRSVPCreate(response=SessionResponse.GOING))

    with pytest.raises(SessionCapacityError):
        service.rsvp_session(
            session.id, attendee, SessionRSVPCreate(response=SessionResponse.GOING)
        )

    service.rsvp_session(session.id, attendee, SessionRSVPCreate(response=SessionResponse.WAITLIST))
    service.withdraw_rsvp(session.id, organizer)

    refreshed = service.list_upcoming_sessions(spot.id, current_user_id=str(attendee.id))[0]
    assert refreshed.stats.going == 1
    assert refreshed.user_response == SessionResponse.GOING
