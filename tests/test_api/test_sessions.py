from datetime import datetime, timedelta, timezone

import pytest

from app.core.security import create_access_token, get_password_hash
from app.models.skate_spot import Difficulty, SpotType
from app.models.user import UserCreate
from app.repositories.user_repository import UserRepository


@pytest.fixture
def session_spot_id(client, auth_token):
    payload = {
        "name": "Session API Spot",
        "description": "Spot for session API tests",
        "spot_type": SpotType.STREET.value,
        "difficulty": Difficulty.INTERMEDIATE.value,
        "location": {
            "latitude": 34.05,
            "longitude": -118.25,
            "city": "Los Angeles",
            "country": "USA",
        },
        "is_public": True,
        "requires_permission": False,
    }
    response = client.post(
        "/api/v1/skate-spots/",
        json=payload,
        cookies={"access_token": auth_token},
    )
    assert response.status_code == 201
    return response.json()["id"]


@pytest.fixture
def session_other_token(session_factory):
    db = session_factory()
    try:
        repo = UserRepository(db)
        user_data = UserCreate(
            email="session-attendee@example.com",
            username="sessionattendee",
            password="sessionpass123",
        )
        hashed = get_password_hash("sessionpass123")
        user = repo.create(user_data, hashed)
        token = create_access_token(data={"sub": str(user.id), "username": user.username})
        return token
    finally:
        db.close()


def test_session_rsvp_flow(client, auth_token, session_other_token, session_spot_id):
    start_time = (datetime.now(timezone.utc) + timedelta(hours=2)).replace(microsecond=0).isoformat()
    end_time = (datetime.now(timezone.utc) + timedelta(hours=3)).replace(microsecond=0).isoformat()

    create_response = client.post(
        f"/api/v1/skate-spots/{session_spot_id}/sessions",
        json={
            "title": "Evening Meetup",
            "description": "Warm-up lines",
            "start_time": start_time,
            "end_time": end_time,
            "capacity": 1,
        },
        cookies={"access_token": auth_token},
    )
    assert create_response.status_code == 201
    session_id = create_response.json()["id"]

    host_rsvp = client.post(
        f"/api/v1/sessions/{session_id}/rsvps",
        json={"response": "going"},
        cookies={"access_token": auth_token},
    )
    assert host_rsvp.status_code == 200

    conflict_rsvp = client.post(
        f"/api/v1/sessions/{session_id}/rsvps",
        json={"response": "going"},
        cookies={"access_token": session_other_token},
    )
    assert conflict_rsvp.status_code == 409

    waitlist_rsvp = client.post(
        f"/api/v1/sessions/{session_id}/rsvps",
        json={"response": "waitlist"},
        cookies={"access_token": session_other_token},
    )
    assert waitlist_rsvp.status_code == 200

    withdraw_response = client.delete(
        f"/api/v1/sessions/{session_id}/rsvps",
        cookies={"access_token": auth_token},
    )
    assert withdraw_response.status_code == 200

    list_response = client.get(
        f"/api/v1/skate-spots/{session_spot_id}/sessions",
        cookies={"access_token": session_other_token},
    )
    assert list_response.status_code == 200
    sessions = list_response.json()
    assert len(sessions) == 1
    assert sessions[0]["stats"]["going"] == 1
    assert sessions[0]["user_response"] == "going"
