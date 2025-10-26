"""Unit tests for the check-in repository."""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

from app.db.models import SkateSpotORM, UserORM
from app.repositories.check_in_repository import CheckInCreateData, CheckInRepository


def _create_user(db) -> UserORM:
    user = UserORM(
        id=str(uuid4()),
        email=f"skater-{uuid4()}@example.com",
        username=f"skater_{uuid4().hex[:8]}",
        hashed_password="hashed",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _create_spot(db, owner_id: str) -> SkateSpotORM:
    spot = SkateSpotORM(
        id=str(uuid4()),
        name="Test Plaza",
        description="Urban ledges and rails",
        spot_type="street",
        difficulty="intermediate",
        latitude=40.0,
        longitude=-73.0,
        city="Testville",
        country="Testland",
        user_id=owner_id,
        is_public=True,
        requires_permission=False,
    )
    db.add(spot)
    db.commit()
    db.refresh(spot)
    return spot


def test_create_and_list_active_check_ins(db):
    repo = CheckInRepository(db)
    user = _create_user(db)
    spot = _create_spot(db, user.id)

    expires_at = datetime.utcnow() + timedelta(hours=2)
    repo.create(
        CheckInCreateData(
            spot_id=spot.id,
            user_id=user.id,
            status="arrived",
            message="Locked in!",
            expires_at=expires_at,
        )
    )

    active = repo.list_active_for_spot(spot.id, now=datetime.utcnow())
    assert len(active) == 1
    record = active[0]
    assert record.status == "arrived"
    assert record.message == "Locked in!"
    assert record.ended_at is None


def test_refresh_active_updates_status_and_message(db):
    repo = CheckInRepository(db)
    user = _create_user(db)
    spot = _create_spot(db, user.id)

    expires_at = datetime.utcnow() + timedelta(hours=1)
    check_in = repo.create(
        CheckInCreateData(
            spot_id=spot.id,
            user_id=user.id,
            status="heading",
            message=None,
            expires_at=expires_at,
        )
    )

    updated = repo.refresh_active(
        check_in,
        status="arrived",
        message="Rolling in.",
        expires_at=datetime.utcnow() + timedelta(hours=2),
    )
    assert updated.status == "arrived"
    assert updated.message == "Rolling in."
    assert updated.ended_at is None


def test_mark_ended_sets_timestamp(db):
    repo = CheckInRepository(db)
    user = _create_user(db)
    spot = _create_spot(db, user.id)

    check_in = repo.create(
        CheckInCreateData(
            spot_id=spot.id,
            user_id=user.id,
            status="arrived",
            message=None,
            expires_at=datetime.utcnow() + timedelta(hours=2),
        )
    )

    ended_at = datetime.utcnow()
    updated = repo.mark_ended(check_in, ended_at=ended_at, message="Peacing out.")
    assert updated.ended_at is not None
    assert updated.message == "Peacing out."
