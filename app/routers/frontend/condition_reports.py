"""Condition report widget routers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated
from uuid import UUID  # noqa: TCH003

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import HTMLResponse
from pydantic import ValidationError

if TYPE_CHECKING:
    from starlette.datastructures import FormData

from app.core.dependencies import get_optional_user
from app.db.models import UserORM  # noqa: TCH001
from app.models.condition_report import SpotConditionReportCreate
from app.routers.frontend._shared import templates
from app.services.condition_report_service import (
    ConditionReportNotFoundError,
    ConditionReportPermissionError,
    ConditionReportService,
    ConditionReportSpotNotFoundError,
    get_condition_report_service,
)

router = APIRouter(tags=["frontend"])


def _condition_context(
    request: Request,
    spot_id: UUID,
    service: ConditionReportService,
    current_user: UserORM | None,
    *,
    message: str | None = None,
    error: str | None = None,
):
    """Build template context for the condition report widget."""
    context_error = error
    latest_report = None
    try:
        latest_report = service.get_latest_for_spot(spot_id)
    except ConditionReportSpotNotFoundError:
        if context_error is None:
            context_error = "This skate spot could not be found."

    return {
        "request": request,
        "spot_id": spot_id,
        "latest_report": latest_report,
        "current_user": current_user,
        "message": message,
        "error": context_error,
    }


@router.get(
    "/skate-spots/{spot_id}/conditions-section",
    response_class=HTMLResponse,
)
async def conditions_section(
    request: Request,
    spot_id: UUID,
    service: Annotated[ConditionReportService, Depends(get_condition_report_service)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Render the conditions widget partial for a spot."""
    context = _condition_context(request, spot_id, service, current_user)
    return templates.TemplateResponse("partials/spot_conditions.html", context)


@router.post(
    "/skate-spots/{spot_id}/condition-reports",
    response_class=HTMLResponse,
)
async def submit_condition_report(
    request: Request,
    spot_id: UUID,
    service: Annotated[ConditionReportService, Depends(get_condition_report_service)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Handle HTMX submissions for creating a condition report."""
    if current_user is None:
        context = _condition_context(
            request,
            spot_id,
            service,
            current_user,
            error="You need to log in to report conditions.",
        )
        return templates.TemplateResponse(
            "partials/spot_conditions.html",
            context,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    form: FormData = await request.form()
    overall_status = form.get("overall_status")
    surface_quality = form.get("surface_quality") or None
    crowdedness = form.get("crowdedness") or None
    security = form.get("security") or None
    note = form.get("note") or None

    # Clean up empty string values
    if surface_quality == "":
        surface_quality = None
    if crowdedness == "":
        crowdedness = None
    if security == "":
        security = None
    if note == "":
        note = None

    try:
        payload = SpotConditionReportCreate(
            overall_status=overall_status,
            surface_quality=surface_quality,
            crowdedness=crowdedness,
            security=security,
            note=note,
        )
        service.create_report(spot_id, current_user, payload)
        success_message = f"Reported {payload.overall_status.value} conditions."
        context = _condition_context(
            request,
            spot_id,
            service,
            current_user,
            message=success_message,
        )
        return templates.TemplateResponse("partials/spot_conditions.html", context)
    except (ValueError, ValidationError) as exc:
        context = _condition_context(
            request,
            spot_id,
            service,
            current_user,
            error=f"Invalid condition data: {exc}",
        )
        return templates.TemplateResponse(
            "partials/spot_conditions.html",
            context,
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except ConditionReportSpotNotFoundError as exc:
        context = _condition_context(
            request,
            spot_id,
            service,
            current_user,
            error=str(exc),
        )
        return templates.TemplateResponse(
            "partials/spot_conditions.html",
            context,
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except Exception:
        context = _condition_context(
            request,
            spot_id,
            service,
            current_user,
            error="Unable to record condition report right now.",
        )
        return templates.TemplateResponse(
            "partials/spot_conditions.html",
            context,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


@router.delete(
    "/skate-spots/{spot_id}/condition-reports/{report_id}",
    response_class=HTMLResponse,
)
async def delete_condition_report(
    request: Request,
    spot_id: UUID,
    report_id: UUID,
    service: Annotated[ConditionReportService, Depends(get_condition_report_service)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Handle HTMX submissions for deleting a condition report."""
    if current_user is None:
        return HTMLResponse(status_code=status.HTTP_401_UNAUTHORIZED, content="")

    try:
        service.delete_report(report_id, current_user)
        context = _condition_context(
            request,
            spot_id,
            service,
            current_user,
            message="Condition report deleted.",
        )
        return templates.TemplateResponse("partials/spot_conditions.html", context)
    except ConditionReportNotFoundError:
        return HTMLResponse(status_code=status.HTTP_404_NOT_FOUND, content="")
    except ConditionReportPermissionError as exc:
        context = _condition_context(
            request,
            spot_id,
            service,
            current_user,
            error=str(exc),
        )
        return templates.TemplateResponse(
            "partials/spot_conditions.html",
            context,
            status_code=status.HTTP_403_FORBIDDEN,
        )
