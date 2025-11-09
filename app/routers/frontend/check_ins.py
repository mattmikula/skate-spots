"""Check-in widget routers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated
from uuid import UUID  # noqa: TCH003

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import HTMLResponse
from pydantic import ValidationError

from app.core.dependencies import get_optional_user
from app.db.models import UserORM  # noqa: TCH001
from app.models.check_in import SpotCheckInCreate, SpotCheckInStatus, SpotCheckOut
from app.routers.frontend._shared import templates
from app.services.check_in_service import (
    CheckInService,
    SpotCheckInNotFoundError,
    SpotCheckInPermissionError,
    SpotCheckInSpotNotFoundError,
    get_check_in_service,
)

router = APIRouter(tags=["frontend"])


def _check_in_context(
    request: Request,
    spot_id: UUID,
    check_in_service: CheckInService,
    current_user: UserORM | None,
    *,
    message: str | None = None,
    error: str | None = None,
):
    """Build template context for the check-in widget."""
    current_check_in = None
    context_error = error
    try:
        active_check_ins = check_in_service.list_active(spot_id)
        if current_user:
            current_check_in = check_in_service.get_active_for_user(spot_id, current_user.id)
    except SpotCheckInSpotNotFoundError:
        active_check_ins = []
        if context_error is None:
            context_error = "This skate spot could not be found."

    return {
        "request": request,
        "spot_id": spot_id,
        "active_check_ins": active_check_ins,
        "current_check_in": current_check_in,
        "current_user": current_user,
        "message": message,
        "error": context_error,
    }


@router.get(
    "/skate-spots/{spot_id}/check-ins-section",
    response_class=HTMLResponse,
)
async def check_in_section(
    request: Request,
    spot_id: UUID,
    check_in_service: Annotated[CheckInService, Depends(get_check_in_service)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Render the check-in widget partial for a spot."""
    context = _check_in_context(request, spot_id, check_in_service, current_user)
    return templates.TemplateResponse("partials/spot_check_ins.html", context)


@router.post(
    "/skate-spots/{spot_id}/check-ins",
    response_class=HTMLResponse,
)
async def submit_check_in(
    request: Request,
    spot_id: UUID,
    check_in_service: Annotated[CheckInService, Depends(get_check_in_service)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Handle HTMX submissions for creating or refreshing a check-in."""
    if current_user is None:
        context = _check_in_context(
            request,
            spot_id,
            check_in_service,
            current_user,
            error="You need to log in to share a check-in.",
        )
        return templates.TemplateResponse(
            "partials/spot_check_ins.html",
            context,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    form = await request.form()
    status_value = (form.get("status") or SpotCheckInStatus.ARRIVED.value).strip().lower()
    message = form.get("message")
    ttl_raw = form.get("ttl_minutes")
    ttl_minutes = None
    if ttl_raw:
        try:
            ttl_minutes = int(ttl_raw)
        except ValueError:
            ttl_minutes = None

    try:
        payload = SpotCheckInCreate(
            status=SpotCheckInStatus(status_value),
            message=message,
            ttl_minutes=ttl_minutes,
        )
        check_in_service.check_in(spot_id, current_user, payload)
        status_label = (
            "at the spot" if payload.status is SpotCheckInStatus.ARRIVED else "heading over"
        )
        success_message = f"Shared that you're {status_label}."
        context = _check_in_context(
            request,
            spot_id,
            check_in_service,
            current_user,
            message=success_message,
        )
        return templates.TemplateResponse("partials/spot_check_ins.html", context)
    except (ValueError, ValidationError):
        context = _check_in_context(
            request,
            spot_id,
            check_in_service,
            current_user,
            error="Please choose a valid status.",
        )
        return templates.TemplateResponse(
            "partials/spot_check_ins.html",
            context,
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except SpotCheckInSpotNotFoundError as exc:
        context = _check_in_context(
            request,
            spot_id,
            check_in_service,
            current_user,
            error=str(exc),
        )
        return templates.TemplateResponse(
            "partials/spot_check_ins.html",
            context,
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except (SpotCheckInNotFoundError, SpotCheckInPermissionError):
        context = _check_in_context(
            request,
            spot_id,
            check_in_service,
            current_user,
            error="Unable to record your check-in right now.",
        )
        return templates.TemplateResponse(
            "partials/spot_check_ins.html",
            context,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


@router.post(
    "/skate-spots/{spot_id}/check-ins/{check_in_id}/checkout",
    response_class=HTMLResponse,
)
async def checkout_check_in(
    request: Request,
    spot_id: UUID,
    check_in_id: UUID,
    check_in_service: Annotated[CheckInService, Depends(get_check_in_service)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Handle HTMX submissions for ending a check-in."""
    if current_user is None:
        return HTMLResponse(status_code=status.HTTP_401_UNAUTHORIZED, content="")

    form = await request.form()
    message = form.get("message")

    try:
        payload = SpotCheckOut(message=message)
    except ValidationError:
        payload = SpotCheckOut(message=None)

    try:
        check_in_service.check_out(check_in_id, current_user, payload)
        context = _check_in_context(
            request,
            spot_id,
            check_in_service,
            current_user,
            message="Checked out successfully.",
        )
        return templates.TemplateResponse("partials/spot_check_ins.html", context)
    except SpotCheckInNotFoundError:
        return HTMLResponse(status_code=status.HTTP_404_NOT_FOUND, content="")
    except SpotCheckInPermissionError as exc:
        context = _check_in_context(
            request,
            spot_id,
            check_in_service,
            current_user,
            error=str(exc),
        )
        return templates.TemplateResponse(
            "partials/spot_check_ins.html",
            context,
            status_code=status.HTTP_403_FORBIDDEN,
        )
