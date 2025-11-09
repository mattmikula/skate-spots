"""Comment widget routers."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID  # noqa: TCH003

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse
from pydantic import ValidationError

from app.core.dependencies import get_optional_user
from app.db.models import UserORM  # noqa: TCH001
from app.models.comment import CommentCreate
from app.routers.frontend._shared import templates
from app.services.comment_service import (
    CommentNotFoundError,
    CommentPermissionError,
    CommentService,
    get_comment_service,
)
from app.services.comment_service import (
    SpotNotFoundError as CommentSpotNotFoundError,
)

router = APIRouter(tags=["frontend"])


def _comment_context(
    request: Request,
    spot_id: UUID,
    comments,
    current_user: UserORM | None,
    *,
    message: str | None = None,
    error: str | None = None,
):
    """Shared template context builder for comment partial responses."""
    return {
        "request": request,
        "spot_id": spot_id,
        "comments": comments,
        "current_user": current_user,
        "message": message,
        "error": error,
    }


@router.get(
    "/skate-spots/{spot_id}/comments-section",
    response_class=HTMLResponse,
)
async def comment_section(
    request: Request,
    spot_id: UUID,
    comment_service: Annotated[CommentService, Depends(get_comment_service)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Render the comment list and form snippet for a skate spot."""
    try:
        comments = comment_service.list_comments(spot_id)
    except CommentSpotNotFoundError:
        return templates.TemplateResponse(
            "partials/comment_section.html",
            _comment_context(
                request,
                spot_id,
                [],
                current_user,
                error="This skate spot is no longer available.",
            ),
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return templates.TemplateResponse(
        "partials/comment_section.html",
        _comment_context(request, spot_id, comments, current_user),
    )


@router.post(
    "/skate-spots/{spot_id}/comments",
    response_class=HTMLResponse,
)
async def submit_comment(
    request: Request,
    spot_id: UUID,
    content: Annotated[str, Form()],
    comment_service: Annotated[CommentService, Depends(get_comment_service)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)],
) -> HTMLResponse:
    """Create a comment through the HTMX form and return the refreshed snippet."""
    if current_user is None:
        try:
            comments = comment_service.list_comments(spot_id)
        except CommentSpotNotFoundError:
            return templates.TemplateResponse(
                "partials/comment_section.html",
                _comment_context(
                    request,
                    spot_id,
                    [],
                    current_user,
                    error="This skate spot is no longer available.",
                ),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return templates.TemplateResponse(
            "partials/comment_section.html",
            _comment_context(
                request,
                spot_id,
                comments,
                current_user,
                error="Log in to join the conversation.",
            ),
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    try:
        comment_data = CommentCreate(content=content)
    except ValidationError:
        try:
            comments = comment_service.list_comments(spot_id)
        except CommentSpotNotFoundError:
            return templates.TemplateResponse(
                "partials/comment_section.html",
                _comment_context(
                    request,
                    spot_id,
                    [],
                    current_user,
                    error="This skate spot is no longer available.",
                ),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return templates.TemplateResponse(
            "partials/comment_section.html",
            _comment_context(
                request,
                spot_id,
                comments,
                current_user,
                error="Comments must be between 1 and 1000 characters.",
            ),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    try:
        comments = comment_service.add_comment(spot_id, current_user, comment_data)
    except CommentSpotNotFoundError:
        return templates.TemplateResponse(
            "partials/comment_section.html",
            _comment_context(
                request,
                spot_id,
                [],
                current_user,
                error="This skate spot is no longer available.",
            ),
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return templates.TemplateResponse(
        "partials/comment_section.html",
        _comment_context(
            request,
            spot_id,
            comments,
            current_user,
            message="Comment added!",
        ),
        status_code=status.HTTP_201_CREATED,
    )


@router.delete(
    "/skate-spots/{spot_id}/comments/{comment_id}",
    response_class=HTMLResponse,
)
async def delete_comment(
    request: Request,
    spot_id: UUID,
    comment_id: UUID,
    comment_service: Annotated[CommentService, Depends(get_comment_service)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)],
) -> HTMLResponse:
    """Delete a comment through the HTMX interface and return the refreshed snippet."""
    if current_user is None:
        try:
            comments = comment_service.list_comments(spot_id)
        except CommentSpotNotFoundError:
            return templates.TemplateResponse(
                "partials/comment_section.html",
                _comment_context(
                    request,
                    spot_id,
                    [],
                    current_user,
                    error="This skate spot is no longer available.",
                ),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return templates.TemplateResponse(
            "partials/comment_section.html",
            _comment_context(
                request,
                spot_id,
                comments,
                current_user,
                error="Log in to manage your comments.",
            ),
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    try:
        comments = comment_service.delete_comment(spot_id, comment_id, current_user)
    except CommentSpotNotFoundError:
        return templates.TemplateResponse(
            "partials/comment_section.html",
            _comment_context(
                request,
                spot_id,
                [],
                current_user,
                error="This skate spot is no longer available.",
            ),
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except CommentNotFoundError:
        try:
            comments = comment_service.list_comments(spot_id)
        except CommentSpotNotFoundError:
            return templates.TemplateResponse(
                "partials/comment_section.html",
                _comment_context(
                    request,
                    spot_id,
                    [],
                    current_user,
                    error="This skate spot is no longer available.",
                ),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return templates.TemplateResponse(
            "partials/comment_section.html",
            _comment_context(
                request,
                spot_id,
                comments,
                current_user,
                message="Comment already removed.",
            ),
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except CommentPermissionError:
        try:
            comments = comment_service.list_comments(spot_id)
        except CommentSpotNotFoundError:
            return templates.TemplateResponse(
                "partials/comment_section.html",
                _comment_context(
                    request,
                    spot_id,
                    [],
                    current_user,
                    error="This skate spot is no longer available.",
                ),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return templates.TemplateResponse(
            "partials/comment_section.html",
            _comment_context(
                request,
                spot_id,
                comments,
                current_user,
                error="You can only remove your own comments unless you are an admin.",
            ),
            status_code=status.HTTP_403_FORBIDDEN,
        )

    return templates.TemplateResponse(
        "partials/comment_section.html",
        _comment_context(
            request,
            spot_id,
            comments,
            current_user,
            message="Comment removed.",
        ),
    )
