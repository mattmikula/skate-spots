"""REST API endpoints for spot check-ins."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID  # noqa: TCH003

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from pydantic import BaseModel

from app.core.dependencies import get_current_user, get_optional_user
from app.db.models import UserORM  # noqa: TCH001
from app.models.checkin import Checkin, CheckinCreate, CheckinStats, CheckinSummary
from app.services.checkin_service import (
    CheckinAlreadyExistsError,
    CheckinNotFoundError,
    CheckinService,
    SpotNotFoundError,
    get_checkin_service,
)

router = APIRouter(tags=["checkins"])


class ErrorDetail(BaseModel):
    """Error response detail."""

    detail: str


@router.post(
    "/spots/{spot_id}/checkins",
    response_model=Checkin,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorDetail, "description": "Already checked in today"},
        404: {"model": ErrorDetail, "description": "Spot not found"},
    },
)
async def create_checkin(
    spot_id: UUID,
    body: CheckinCreate,
    current_user: Annotated[UserORM, Depends(get_current_user)],
    service: Annotated[CheckinService, Depends(get_checkin_service)],
) -> Checkin:
    """Create a new check-in for the current user at a spot.

    One check-in per user per spot per day is allowed.
    """

    try:
        return service.create_checkin(spot_id, current_user.id, body.notes)
    except CheckinAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except SpotNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get(
    "/spots/{spot_id}/checkins/stats",
    response_model=CheckinStats,
    responses={
        404: {"model": ErrorDetail, "description": "Spot not found"},
    },
)
async def get_checkin_stats(
    spot_id: UUID,
    current_user: Annotated[UserORM | None, Depends(get_optional_user)],
    service: Annotated[CheckinService, Depends(get_checkin_service)],
) -> CheckinStats:
    """Get check-in statistics for a spot."""

    user_id = current_user.id if current_user else None
    return service.get_spot_stats(spot_id, user_id)


@router.get(
    "/spots/{spot_id}/checkins",
    response_model=list[Checkin],
    responses={
        404: {"model": ErrorDetail, "description": "Spot not found"},
    },
)
async def list_spot_checkins(
    spot_id: UUID,
    service: Annotated[CheckinService, Depends(get_checkin_service)],
    limit: int = 20,
) -> list[Checkin]:
    """Get recent check-ins for a spot."""

    return service.get_spot_recent_checkins(spot_id, limit)


@router.get(
    "/users/me/checkins",
    response_model=list[CheckinSummary],
)
async def get_my_checkins(
    current_user: Annotated[UserORM, Depends(get_current_user)],
    service: Annotated[CheckinService, Depends(get_checkin_service)],
    limit: int = 50,
) -> list[CheckinSummary]:
    """Get the current user's check-in history."""

    return service.get_user_history(current_user.id, limit)


@router.delete(
    "/checkins/{checkin_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        403: {"description": "Permission denied"},
        404: {"description": "Check-in not found"},
    },
)
async def delete_checkin(
    checkin_id: UUID,
    current_user: Annotated[UserORM, Depends(get_current_user)],
    service: Annotated[CheckinService, Depends(get_checkin_service)],
) -> Response:
    """Delete a check-in.

    Only the user who created it or admins can delete.
    """

    try:
        service.delete_checkin(checkin_id, current_user.id, current_user.is_admin)
    except CheckinNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e

    return Response(status_code=status.HTTP_204_NO_CONTENT)
