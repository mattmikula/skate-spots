"""API endpoints for skate spot comments."""

from __future__ import annotations

import uuid  # noqa: TC003
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.core.dependencies import get_current_user, get_optional_user
from app.core.rate_limiter import SKATE_SPOT_WRITE_LIMIT, rate_limited
from app.db.models import UserORM  # noqa: TC001
from app.models.comment import Comment, CommentCreate
from app.services.comment_service import (
    CommentNotFoundError,
    CommentPermissionError,
    CommentService,
    SpotNotFoundError,
    get_comment_service,
)

router = APIRouter(prefix="/skate-spots/{spot_id}/comments", tags=["comments"])


def _handle_spot_missing(exc: SpotNotFoundError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/", response_model=list[Comment])
async def list_comments(
    spot_id: uuid.UUID,
    service: Annotated[CommentService, Depends(get_comment_service)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> list[Comment]:
    """Return comments for a skate spot."""

    del current_user  # unused but retained for parity with authenticated routes
    try:
        return service.list_comments(spot_id)
    except SpotNotFoundError as exc:  # pragma: no cover - defensive
        raise _handle_spot_missing(exc) from exc


@router.post(
    "/",
    response_model=list[Comment],
    status_code=status.HTTP_201_CREATED,
    dependencies=[rate_limited(SKATE_SPOT_WRITE_LIMIT)],
)
async def create_comment(
    spot_id: uuid.UUID,
    payload: CommentCreate,
    service: Annotated[CommentService, Depends(get_comment_service)],
    current_user: Annotated[UserORM, Depends(get_current_user)],
) -> list[Comment]:
    """Create a new comment and return the updated list."""

    try:
        return service.add_comment(spot_id, current_user, payload)
    except SpotNotFoundError as exc:
        raise _handle_spot_missing(exc) from exc


@router.delete(
    "/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[rate_limited(SKATE_SPOT_WRITE_LIMIT)],
)
async def delete_comment(
    spot_id: uuid.UUID,
    comment_id: uuid.UUID,
    service: Annotated[CommentService, Depends(get_comment_service)],
    current_user: Annotated[UserORM, Depends(get_current_user)],
) -> Response:
    """Delete a comment if the user has permission."""

    try:
        service.delete_comment(spot_id, comment_id, current_user)
    except SpotNotFoundError as exc:
        raise _handle_spot_missing(exc) from exc
    except CommentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except CommentPermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)
