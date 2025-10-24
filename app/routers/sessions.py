"""REST API endpoints for session scheduling."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID  # noqa: TCH003

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.core.dependencies import get_current_user, get_optional_user
from app.core.rate_limiter import SKATE_SPOT_WRITE_LIMIT, rate_limited
from app.db.models import UserORM  # noqa: TCH001
from app.models.session import Session, SessionCreate, SessionRSVPCreate, SessionUpdate
from app.services.activity_service import ActivityService, get_activity_service
from app.services.session_service import (
    SessionCapacityError,
    SessionInactiveError,
    SessionNotFoundError,
    SessionPermissionError,
    SessionRSVPNotFoundError,
    SessionService,
    SessionSpotNotFoundError,
    get_session_service,
)

router = APIRouter(tags=["sessions"])


def _get_session_service_with_activity(
    session_service: Annotated[SessionService, Depends(get_session_service)],
    activity_service: Annotated[ActivityService, Depends(get_activity_service)],
) -> SessionService:
    """Provide session service with activity service injected."""
    session_service.set_activity_service(activity_service)
    return session_service


def _map_service_error(error: Exception) -> HTTPException:
    if isinstance(error, SessionSpotNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
    if isinstance(error, SessionNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
    if isinstance(error, SessionPermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error))
    if isinstance(error, SessionCapacityError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))
    if isinstance(error, SessionInactiveError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))
    if isinstance(error, SessionRSVPNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.get("/skate-spots/{spot_id}/sessions", response_model=list[Session])
async def list_spot_sessions(
    spot_id: UUID,
    service: Annotated[SessionService, Depends(get_session_service)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> list[Session]:
    """Return scheduled sessions for the given skate spot."""

    try:
        return service.list_upcoming_sessions(
            spot_id, current_user_id=str(current_user.id) if current_user else None
        )
    except Exception as exc:  # noqa: BLE001
        raise _map_service_error(exc) from exc


@router.post(
    "/skate-spots/{spot_id}/sessions",
    response_model=Session,
    status_code=status.HTTP_201_CREATED,
    dependencies=[rate_limited(SKATE_SPOT_WRITE_LIMIT)],
)
async def create_spot_session(
    spot_id: UUID,
    payload: SessionCreate,
    service: Annotated[SessionService, Depends(_get_session_service_with_activity)],
    current_user: Annotated[UserORM, Depends(get_current_user)],
) -> Session:
    """Create a session for a spot."""

    try:
        return service.create_session(spot_id, current_user, payload)
    except Exception as exc:  # noqa: BLE001
        raise _map_service_error(exc) from exc


@router.patch("/sessions/{session_id}", response_model=Session)
async def update_session(
    session_id: UUID,
    payload: SessionUpdate,
    service: Annotated[SessionService, Depends(get_session_service)],
    current_user: Annotated[UserORM, Depends(get_current_user)],
) -> Session:
    """Update details for a session."""

    try:
        return service.update_session(session_id, current_user, payload)
    except Exception as exc:  # noqa: BLE001
        raise _map_service_error(exc) from exc


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: UUID,
    service: Annotated[SessionService, Depends(get_session_service)],
    current_user: Annotated[UserORM, Depends(get_current_user)],
) -> Response:
    """Delete a session."""

    try:
        service.delete_session(session_id, current_user)
    except Exception as exc:  # noqa: BLE001
        raise _map_service_error(exc) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/sessions/{session_id}/rsvps", response_model=Session)
async def rsvp_session(
    session_id: UUID,
    payload: SessionRSVPCreate,
    service: Annotated[SessionService, Depends(_get_session_service_with_activity)],
    current_user: Annotated[UserORM, Depends(get_current_user)],
) -> Session:
    """Create or update the current user's RSVP."""

    try:
        return service.rsvp_session(session_id, current_user, payload)
    except Exception as exc:  # noqa: BLE001
        raise _map_service_error(exc) from exc


@router.delete("/sessions/{session_id}/rsvps", response_model=Session)
async def withdraw_rsvp(
    session_id: UUID,
    service: Annotated[SessionService, Depends(get_session_service)],
    current_user: Annotated[UserORM, Depends(get_current_user)],
) -> Session:
    """Withdraw the authenticated user's RSVP."""

    try:
        return service.withdraw_rsvp(session_id, current_user)
    except Exception as exc:  # noqa: BLE001
        raise _map_service_error(exc) from exc
