"""REST API endpoints for spot check-ins."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID  # noqa: TCH003

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_current_user
from app.core.rate_limiter import SKATE_SPOT_WRITE_LIMIT, rate_limited
from app.db.models import UserORM  # noqa: TCH001
from app.models.check_in import SpotCheckIn, SpotCheckInCreate, SpotCheckOut
from app.services.check_in_service import (
    CheckInService,
    SpotCheckInNotFoundError,
    SpotCheckInPermissionError,
    SpotCheckInSpotNotFoundError,
    get_check_in_service,
)

router = APIRouter(tags=["check-ins"])


def _map_check_in_error(exc: Exception) -> HTTPException:
    if isinstance(exc, SpotCheckInSpotNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, SpotCheckInNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, SpotCheckInPermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/skate-spots/{spot_id}/check-ins", response_model=list[SpotCheckIn])
async def list_spot_check_ins(
    spot_id: UUID,
    service: Annotated[CheckInService, Depends(get_check_in_service)],
) -> list[SpotCheckIn]:
    """Return active check-ins for the given skate spot."""

    try:
        return service.list_active(spot_id)
    except Exception as exc:  # noqa: BLE001
        raise _map_check_in_error(exc) from exc


@router.post(
    "/skate-spots/{spot_id}/check-ins",
    response_model=SpotCheckIn,
    dependencies=[rate_limited(SKATE_SPOT_WRITE_LIMIT)],
)
async def create_spot_check_in(
    spot_id: UUID,
    payload: SpotCheckInCreate,
    service: Annotated[CheckInService, Depends(get_check_in_service)],
    current_user: Annotated[UserORM, Depends(get_current_user)],
) -> SpotCheckIn:
    """Create or refresh a check-in for the authenticated user."""

    try:
        return service.check_in(spot_id, current_user, payload)
    except Exception as exc:  # noqa: BLE001
        raise _map_check_in_error(exc) from exc


@router.post("/check-ins/{check_in_id}/checkout", response_model=SpotCheckIn)
async def checkout_spot_check_in(
    check_in_id: UUID,
    service: Annotated[CheckInService, Depends(get_check_in_service)],
    current_user: Annotated[UserORM, Depends(get_current_user)],
    payload: SpotCheckOut | None = None,
) -> SpotCheckIn:
    """End the active check-in."""

    try:
        return service.check_out(check_in_id, current_user, payload)
    except Exception as exc:  # noqa: BLE001
        raise _map_check_in_error(exc) from exc
