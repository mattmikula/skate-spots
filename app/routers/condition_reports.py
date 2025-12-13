"""REST API endpoints for spot condition reports."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.core.dependencies import get_current_user
from app.core.rate_limiter import SKATE_SPOT_WRITE_LIMIT, rate_limited
from app.db.models import UserORM
from app.models.condition_report import SpotConditionReport, SpotConditionReportCreate
from app.services.condition_report_service import (
    ConditionReportError,
    ConditionReportNotFoundError,
    ConditionReportPermissionError,
    ConditionReportService,
    ConditionReportSpotNotFoundError,
    get_condition_report_service,
)

router = APIRouter(prefix="/api/v1", tags=["condition-reports"])


@router.post(
    "/skate-spots/{spot_id}/condition-reports",
    response_model=SpotConditionReport,
    status_code=status.HTTP_201_CREATED,
    dependencies=[rate_limited(SKATE_SPOT_WRITE_LIMIT)],
)
def create_condition_report(
    spot_id: UUID,
    payload: SpotConditionReportCreate,
    current_user: Annotated[UserORM, Depends(get_current_user)],
    service: Annotated[ConditionReportService, Depends(get_condition_report_service)],
) -> SpotConditionReport:
    """Create a new condition report for a spot.

    Requires authentication. Rate limited to prevent spam.
    Reports expire after 24 hours.
    """
    try:
        return service.create_report(spot_id, current_user, payload)
    except ConditionReportSpotNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ConditionReportError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "/skate-spots/{spot_id}/condition-reports/latest",
    response_model=SpotConditionReport | None,
)
def get_latest_condition_report(
    spot_id: UUID,
    service: Annotated[ConditionReportService, Depends(get_condition_report_service)],
) -> SpotConditionReport | None:
    """Get the latest active condition report for a spot.

    Returns None if no active reports exist.
    Public endpoint - no authentication required.
    """
    try:
        return service.get_latest_for_spot(spot_id)
    except ConditionReportSpotNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/skate-spots/{spot_id}/condition-reports",
    response_model=list[SpotConditionReport],
)
def list_condition_reports(
    spot_id: UUID,
    service: Annotated[ConditionReportService, Depends(get_condition_report_service)],
    limit: int = 10,
) -> list[SpotConditionReport]:
    """List recent active condition reports for a spot.

    Returns up to `limit` reports, ordered by creation time (newest first).
    Public endpoint - no authentication required.
    """
    try:
        return service.list_for_spot(spot_id, limit=min(limit, 50))
    except ConditionReportSpotNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.delete(
    "/condition-reports/{report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_condition_report(
    report_id: UUID,
    current_user: Annotated[UserORM, Depends(get_current_user)],
    service: Annotated[ConditionReportService, Depends(get_condition_report_service)],
) -> Response:
    """Delete a condition report.

    Only the report author or an admin can delete a report.
    This is a soft delete - the report is marked as deleted but not removed from the database.
    """
    try:
        service.delete_report(report_id, current_user)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ConditionReportNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ConditionReportPermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
