"""Tests for the check-in service logic."""

from __future__ import annotations

from app.models.check_in import SpotCheckInCreate, SpotCheckInStatus, SpotCheckOut
from app.models.skate_spot import Difficulty, Location, SkateSpotCreate, SpotType
from app.models.user import UserCreate
from app.repositories.skate_spot_repository import SkateSpotRepository
from app.repositories.user_repository import UserRepository
from app.services.activity_service import ActivityService
from app.services.check_in_service import CheckInService


def _create_user(db, email: str, username: str):
    repo = UserRepository(db)
    user = repo.create(
        UserCreate(email=email, username=username, password="changeme123"),
        hashed_password="hashed",
    )
    db.expunge(user)
    return user


def _create_spot(session_factory, owner_id: str):
    spot_repo = SkateSpotRepository(session_factory=session_factory)
    spot = spot_repo.create(
        SkateSpotCreate(
            name="Downtown Plaza",
            description="Stairs, rails, and smooth marble.",
            spot_type=SpotType.STREET,
            difficulty=Difficulty.INTERMEDIATE,
            location=Location(
                latitude=34.0522,
                longitude=-118.2437,
                city="Los Angeles",
                country="USA",
            ),
            photos=[],
        ),
        owner_id,
    )
    return spot


def test_check_in_create_and_list(session_factory):
    with session_factory() as db:
        service = CheckInService(db)
        skater = _create_user(db, "skater@example.com", "kickflip_kid")
        spot = _create_spot(session_factory, skater.id)

        payload = SpotCheckInCreate(status=SpotCheckInStatus.ARRIVED, message="Session on!")
        created = service.check_in(spot.id, skater, payload)

        assert created.status is SpotCheckInStatus.ARRIVED
        assert created.message == "Session on!"

        active = service.list_active(spot.id)
        assert len(active) == 1
        assert active[0].id == created.id


def test_check_in_refreshes_existing_record(session_factory):
    with session_factory() as db:
        service = CheckInService(db)
        skater = _create_user(db, "skater2@example.com", "nollie_nerd")
        spot = _create_spot(session_factory, skater.id)

        first = service.check_in(
            spot.id,
            skater,
            SpotCheckInCreate(status=SpotCheckInStatus.HEADING, message=None),
        )
        refreshed = service.check_in(
            spot.id,
            skater,
            SpotCheckInCreate(status=SpotCheckInStatus.ARRIVED, message="Made it"),
        )

        assert refreshed.id == first.id
        assert refreshed.status is SpotCheckInStatus.ARRIVED
        assert refreshed.message == "Made it"
        active = service.list_active(spot.id)
        assert len(active) == 1
        assert active[0].status is SpotCheckInStatus.ARRIVED


def test_check_out_marks_record_inactive(session_factory):
    with session_factory() as db:
        service = CheckInService(db)
        skater = _create_user(db, "skater3@example.com", "manual_master")
        spot = _create_spot(session_factory, skater.id)

        created = service.check_in(
            spot.id,
            skater,
            SpotCheckInCreate(status=SpotCheckInStatus.ARRIVED, message=None),
        )
        ended = service.check_out(
            created.id, skater, SpotCheckOut(message="Heading to another park")
        )

        assert ended.is_active is False
        assert ended.ended_at is not None
        assert ended.message == "Heading to another park"
        assert service.list_active(spot.id) == []


def test_check_in_records_activity(session_factory):
    with session_factory() as db:
        activity_service = ActivityService(db)
        service = CheckInService(db, activity_service=activity_service)
        skater = _create_user(db, "skater4@example.com", "grind_guru")
        spot = _create_spot(session_factory, skater.id)

        service.check_in(
            spot.id,
            skater,
            SpotCheckInCreate(status=SpotCheckInStatus.HEADING, message=None, ttl_minutes=30),
        )

        activities, _ = activity_service.activity_repository.get_user_activity(skater.id, limit=5)
        assert any(activity.activity_type == "spot_checked_in" for activity in activities)
