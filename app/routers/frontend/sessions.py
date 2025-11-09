"""Session scheduling and RSVP routers."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID  # noqa: TCH003

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from pydantic import ValidationError

from app.core.dependencies import get_optional_user
from app.db.models import UserORM  # noqa: TCH001
from app.models.session import (
    SessionCreate,
    SessionResponse,
    SessionRSVPCreate,
    SessionStatus,
)
from app.routers.frontend._shared import _format_validation_errors, templates
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
from app.services.skate_spot_service import SkateSpotService, get_skate_spot_service

router = APIRouter(tags=["frontend"])


def _get_session_service_with_activity(
    session_service: Annotated[SessionService, Depends(get_session_service)],
    activity_service: Annotated[ActivityService, Depends(get_activity_service)],
) -> SessionService:
    """Provide session service with activity service injected."""
    session_service.set_activity_service(activity_service)
    return session_service


async def _session_context(
    request: Request,
    spot_id: UUID,
    session_service: SessionService,
    current_user: UserORM | None,
    *,
    message: str | None = None,
    error: str | None = None,
    form_errors: dict[str, list[str]] | None = None,
    form_data: dict[str, str] | None = None,
):
    """Build template context for the session HTMX partial."""
    context_error = error
    try:
        sessions = await session_service.list_upcoming_sessions(
            spot_id, current_user_id=str(current_user.id) if current_user else None
        )
    except SessionSpotNotFoundError:
        sessions = []
        if context_error is None:
            context_error = "This skate spot is no longer available."

    return {
        "request": request,
        "spot_id": spot_id,
        "sessions": sessions,
        "current_user": current_user,
        "message": message,
        "error": context_error,
        "form_errors": form_errors or {},
        "form_data": form_data or {},
        "SessionResponse": SessionResponse,
        "SessionStatus": SessionStatus,
    }


def _session_form_payload(form) -> tuple[dict[str, object], dict[str, str]]:
    """Extract the payload and redisplay data for the session create form."""
    fields = [
        "title",
        "description",
        "start_time",
        "end_time",
        "meet_location",
        "skill_level",
        "capacity",
    ]
    form_data = {field: (form.get(field) or "").strip() for field in fields}
    payload: dict[str, object] = {
        "title": form_data["title"],
        "description": form_data["description"] or None,
        "start_time": form_data["start_time"],
        "end_time": form_data["end_time"],
        "meet_location": form_data["meet_location"] or None,
        "skill_level": form_data["skill_level"] or None,
        "capacity": form_data["capacity"] or None,
    }
    if not form_data["capacity"]:
        payload["capacity"] = None
    return payload, form_data


@router.get(
    "/skate-spots/{spot_id}/sessions-section",
    response_class=HTMLResponse,
)
async def session_section(
    request: Request,
    spot_id: UUID,
    session_service: Annotated[SessionService, Depends(_get_session_service_with_activity)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Render the session list and form snippet for a skate spot."""
    context = await _session_context(request, spot_id, session_service, current_user)
    return templates.TemplateResponse("partials/session_list.html", context)


@router.get(
    "/skate-spots/{spot_id}/sessions/{session_id}",
    response_class=HTMLResponse,
)
async def session_detail(
    request: Request,
    spot_id: UUID,
    session_id: UUID,
    skate_spot_service: Annotated[SkateSpotService, Depends(get_skate_spot_service)],
    session_service: Annotated[SessionService, Depends(_get_session_service_with_activity)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Display a single session detail page."""
    try:
        spot = skate_spot_service.get_spot(spot_id)
        if spot is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spot not found")
    except HTTPException:
        raise

    try:
        session = await session_service.get_session(
            session_id, current_user_id=str(current_user.id) if current_user else None
        )
    except SessionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        ) from exc

    return templates.TemplateResponse(
        "session_detail.html",
        {
            "request": request,
            "spot": spot,
            "session": session,
            "current_user": current_user,
            "SessionResponse": SessionResponse,
            "SessionStatus": SessionStatus,
        },
    )


@router.post(
    "/skate-spots/{spot_id}/sessions",
    response_class=HTMLResponse,
)
async def create_session_partial(
    request: Request,
    spot_id: UUID,
    session_service: Annotated[SessionService, Depends(_get_session_service_with_activity)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Handle creation of a new session via HTMX."""
    if current_user is None:
        context = await _session_context(
            request,
            spot_id,
            session_service,
            current_user,
            error="Log in to organise a session.",
        )
        return templates.TemplateResponse(
            "partials/session_list.html",
            context,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    form = await request.form()
    payload_dict, redisplay = _session_form_payload(form)

    try:
        payload = SessionCreate(**payload_dict)
    except ValidationError as error:
        context = await _session_context(
            request,
            spot_id,
            session_service,
            current_user,
            form_errors=_format_validation_errors(error),
            form_data=redisplay,
        )
        return templates.TemplateResponse(
            "partials/session_list.html",
            context,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    try:
        await session_service.create_session(spot_id, current_user, payload)
    except SessionSpotNotFoundError as exc:
        context = await _session_context(
            request,
            spot_id,
            session_service,
            current_user,
            error=str(exc),
            form_data=redisplay,
        )
        return templates.TemplateResponse(
            "partials/session_list.html",
            context,
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except SessionPermissionError as exc:
        context = await _session_context(
            request,
            spot_id,
            session_service,
            current_user,
            error=str(exc),
            form_data=redisplay,
        )
        return templates.TemplateResponse(
            "partials/session_list.html",
            context,
            status_code=status.HTTP_403_FORBIDDEN,
        )
    except ValueError as exc:
        context = await _session_context(
            request,
            spot_id,
            session_service,
            current_user,
            error=str(exc),
            form_data=redisplay,
        )
        return templates.TemplateResponse(
            "partials/session_list.html",
            context,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    context = await _session_context(
        request,
        spot_id,
        session_service,
        current_user,
        message="Session scheduled!",
    )
    return templates.TemplateResponse(
        "partials/session_list.html",
        context,
        status_code=status.HTTP_201_CREATED,
    )


@router.post(
    "/skate-spots/{spot_id}/sessions/{session_id}/rsvp",
    response_class=HTMLResponse,
)
async def submit_session_rsvp(
    request: Request,
    spot_id: UUID,
    session_id: UUID,
    session_service: Annotated[SessionService, Depends(_get_session_service_with_activity)],
    response_choice: Annotated[str, Form()],
    note: Annotated[str | None, Form()] = None,
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Create or update an RSVP via HTMX."""
    if current_user is None:
        context = await _session_context(
            request,
            spot_id,
            session_service,
            current_user,
            error="Log in to RSVP.",
        )
        return templates.TemplateResponse(
            "partials/session_list.html",
            context,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    try:
        response_value = SessionResponse(response_choice)
    except ValueError:
        context = await _session_context(
            request,
            spot_id,
            session_service,
            current_user,
            error="Invalid RSVP selection.",
        )
        return templates.TemplateResponse(
            "partials/session_list.html",
            context,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    payload = SessionRSVPCreate(response=response_value, note=note)

    try:
        await session_service.rsvp_session(session_id, current_user, payload)
        context = await _session_context(
            request,
            spot_id,
            session_service,
            current_user,
            message="RSVP updated!",
        )
        status_code = status.HTTP_200_OK
    except SessionCapacityError as exc:
        context = await _session_context(
            request,
            spot_id,
            session_service,
            current_user,
            error=str(exc),
        )
        status_code = status.HTTP_409_CONFLICT
    except SessionInactiveError as exc:
        context = await _session_context(
            request,
            spot_id,
            session_service,
            current_user,
            error=str(exc),
        )
        status_code = status.HTTP_400_BAD_REQUEST
    except SessionNotFoundError as exc:
        context = await _session_context(
            request,
            spot_id,
            session_service,
            current_user,
            error=str(exc),
        )
        status_code = status.HTTP_404_NOT_FOUND
    except SessionPermissionError as exc:
        context = await _session_context(
            request,
            spot_id,
            session_service,
            current_user,
            error=str(exc),
        )
        status_code = status.HTTP_403_FORBIDDEN
    except SessionSpotNotFoundError as exc:
        context = await _session_context(
            request,
            spot_id,
            session_service,
            current_user,
            error=str(exc),
        )
        status_code = status.HTTP_404_NOT_FOUND

    return templates.TemplateResponse(
        "partials/session_list.html",
        context,
        status_code=status_code,
    )


@router.delete(
    "/skate-spots/{spot_id}/sessions/{session_id}/rsvp",
    response_class=HTMLResponse,
)
async def withdraw_session_rsvp(
    request: Request,
    spot_id: UUID,
    session_id: UUID,
    session_service: Annotated[SessionService, Depends(_get_session_service_with_activity)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Withdraw the current user's RSVP."""
    if current_user is None:
        context = await _session_context(
            request,
            spot_id,
            session_service,
            current_user,
            error="Log in to manage your RSVP.",
        )
        return templates.TemplateResponse(
            "partials/session_list.html",
            context,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    try:
        await session_service.withdraw_rsvp(session_id, current_user)
        context = await _session_context(
            request,
            spot_id,
            session_service,
            current_user,
            message="RSVP withdrawn.",
        )
        status_code = status.HTTP_200_OK
    except SessionRSVPNotFoundError as exc:
        context = await _session_context(
            request,
            spot_id,
            session_service,
            current_user,
            error=str(exc),
        )
        status_code = status.HTTP_404_NOT_FOUND
    except (SessionNotFoundError, SessionSpotNotFoundError) as exc:
        context = await _session_context(
            request,
            spot_id,
            session_service,
            current_user,
            error=str(exc),
        )
        status_code = status.HTTP_404_NOT_FOUND
    except SessionPermissionError as exc:
        context = await _session_context(
            request,
            spot_id,
            session_service,
            current_user,
            error=str(exc),
        )
        status_code = status.HTTP_403_FORBIDDEN

    return templates.TemplateResponse(
        "partials/session_list.html",
        context,
        status_code=status_code,
    )


@router.post(
    "/skate-spots/{spot_id}/sessions/{session_id}/cancel",
    response_class=HTMLResponse,
)
async def cancel_session_partial(
    request: Request,
    spot_id: UUID,
    session_id: UUID,
    session_service: Annotated[SessionService, Depends(_get_session_service_with_activity)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Allow organisers or admins to cancel a session."""
    if current_user is None:
        context = await _session_context(
            request,
            spot_id,
            session_service,
            current_user,
            error="Log in to manage this session.",
        )
        return templates.TemplateResponse(
            "partials/session_list.html",
            context,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    try:
        await session_service.change_status(session_id, current_user, SessionStatus.CANCELLED)
        context = await _session_context(
            request,
            spot_id,
            session_service,
            current_user,
            message="Session cancelled.",
        )
        status_code = status.HTTP_200_OK
    except SessionPermissionError as exc:
        context = await _session_context(
            request,
            spot_id,
            session_service,
            current_user,
            error=str(exc),
        )
        status_code = status.HTTP_403_FORBIDDEN
    except (SessionNotFoundError, SessionSpotNotFoundError) as exc:
        context = await _session_context(
            request,
            spot_id,
            session_service,
            current_user,
            error=str(exc),
        )
        status_code = status.HTTP_404_NOT_FOUND

    return templates.TemplateResponse(
        "partials/session_list.html",
        context,
        status_code=status_code,
    )
