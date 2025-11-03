from datetime import UTC, datetime, timedelta

import pytest

from app.models.session import SessionCreate, SessionResponse, SessionRSVPCreate
from app.models.skate_spot import Difficulty, Location, SkateSpotCreate, SpotType
from app.models.user import UserCreate
from app.repositories.session_repository import SessionRepository
from app.repositories.skate_spot_repository import SkateSpotRepository
from app.repositories.user_repository import UserRepository
from app.services.activity_service import ActivityService
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


def _service(session_factory, async_session_factory, activity_service=None) -> SessionService:
    return SessionService(
        SessionRepository(session_factory=async_session_factory),
        SkateSpotRepository(session_factory=session_factory),
        activity_service=activity_service,
    )


@pytest.mark.asyncio
async def test_create_and_list_session(session_factory, async_session_factory):
    service = _service(session_factory, async_session_factory)
    organizer = _create_user(session_factory, "organizer@example.com", "organizer")
    spot = _create_spot(session_factory, organizer.id)

    payload = SessionCreate(
        title="Sunrise Flow",
        description="Warm-up laps",
        start_time=datetime.now(UTC) + timedelta(hours=2),
        end_time=datetime.now(UTC) + timedelta(hours=3),
        meet_location="Main gate",
        skill_level="Beginner",
        capacity=6,
    )

    session = await service.create_session(spot.id, organizer, payload)
    assert session.title == "Sunrise Flow"
    listed = await service.list_upcoming_sessions(spot.id, current_user_id=str(organizer.id))
    assert len(listed) == 1
    assert listed[0].stats.going == 0
    assert listed[0].user_response is None


@pytest.mark.asyncio
async def test_waitlist_promotion_after_withdraw(session_factory, async_session_factory):
    service = _service(session_factory, async_session_factory)
    organizer = _create_user(session_factory, "organizer@example.com", "organizer")
    attendee = _create_user(session_factory, "attendee@example.com", "attendee")
    spot = _create_spot(session_factory, organizer.id)

    payload = SessionCreate(
        title="Capacity Test",
        description="",
        start_time=datetime.now(UTC) + timedelta(hours=1),
        end_time=datetime.now(UTC) + timedelta(hours=2),
        capacity=1,
    )
    session = await service.create_session(spot.id, organizer, payload)

    await service.rsvp_session(
        session.id, organizer, SessionRSVPCreate(response=SessionResponse.GOING)
    )

    with pytest.raises(SessionCapacityError):
        await service.rsvp_session(
            session.id, attendee, SessionRSVPCreate(response=SessionResponse.GOING)
        )

    await service.rsvp_session(
        session.id, attendee, SessionRSVPCreate(response=SessionResponse.WAITLIST)
    )
    await service.withdraw_rsvp(session.id, organizer)

    refreshed = (await service.list_upcoming_sessions(spot.id, current_user_id=str(attendee.id)))[0]
    assert refreshed.stats.going == 1
    assert refreshed.user_response == SessionResponse.GOING


@pytest.mark.asyncio
async def test_session_creation_records_activity(session_factory, async_session_factory):
    organizer = _create_user(session_factory, "organizer@example.com", "organizer")
    spot = _create_spot(session_factory, organizer.id)

    # Create activity service
    db = session_factory()
    try:
        activity_service = ActivityService(db)
        service_with_activity = SessionService(
            SessionRepository(session_factory=async_session_factory),
            SkateSpotRepository(session_factory=session_factory),
            activity_service=activity_service,
        )

        payload = SessionCreate(
            title="Sunrise Flow",
            description="Warm-up laps",
            start_time=datetime.now(UTC) + timedelta(hours=2),
            end_time=datetime.now(UTC) + timedelta(hours=3),
            capacity=6,
        )

        session = await service_with_activity.create_session(spot.id, organizer, payload)
        assert session.title == "Sunrise Flow"

        # Verify activity was recorded
        activities, _ = activity_service.activity_repository.get_user_activity(
            organizer.id, limit=1
        )
        assert len(activities) > 0
        assert activities[0].activity_type == "session_created"
    finally:
        db.close()


@pytest.mark.asyncio
async def test_session_rsvp_records_activity(session_factory, async_session_factory):
    service = _service(session_factory, async_session_factory)
    organizer = _create_user(session_factory, "organizer@example.com", "organizer")
    attendee = _create_user(session_factory, "attendee@example.com", "attendee")
    spot = _create_spot(session_factory, organizer.id)

    payload = SessionCreate(
        title="Capacity Test",
        description="",
        start_time=datetime.now(UTC) + timedelta(hours=1),
        end_time=datetime.now(UTC) + timedelta(hours=2),
        capacity=10,
    )
    session = await service.create_session(spot.id, organizer, payload)

    # Create activity service and update service
    db = session_factory()
    try:
        activity_service = ActivityService(db)
        service_with_activity = SessionService(
            SessionRepository(session_factory=async_session_factory),
            SkateSpotRepository(session_factory=session_factory),
            activity_service=activity_service,
        )

        await service_with_activity.rsvp_session(
            session.id, attendee, SessionRSVPCreate(response=SessionResponse.GOING)
        )

        # Verify activity was recorded
        activities, _ = activity_service.activity_repository.get_user_activity(attendee.id, limit=1)
        assert len(activities) > 0
        assert activities[0].activity_type == "session_rsvp"
    finally:
        db.close()
