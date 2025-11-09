"""Rating widget routers."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID  # noqa: TCH003

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse

from app.core.dependencies import get_optional_user
from app.db.models import UserORM  # noqa: TCH001
from app.models.rating import RatingCreate
from app.routers.frontend._shared import templates
from app.services.rating_service import (
    RatingNotFoundError,
    RatingService,
    get_rating_service,
)
from app.services.rating_service import (
    SpotNotFoundError as RatingSpotNotFoundError,
)

router = APIRouter(tags=["frontend"])


@router.get(
    "/skate-spots/{spot_id}/rating-section",
    response_class=HTMLResponse,
)
async def rating_section(
    request: Request,
    spot_id: UUID,
    rating_service: Annotated[RatingService, Depends(get_rating_service)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Render the rating summary and form snippet for a skate spot."""
    try:
        summary = rating_service.get_summary(spot_id, current_user.id if current_user else None)
    except RatingSpotNotFoundError:
        return templates.TemplateResponse(
            "partials/rating_section.html",
            {
                "request": request,
                "spot_id": spot_id,
                "summary": None,
                "current_user": current_user,
                "error": "This skate spot is no longer available.",
            },
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return templates.TemplateResponse(
        "partials/rating_section.html",
        {
            "request": request,
            "spot_id": spot_id,
            "summary": summary,
            "current_user": current_user,
            "message": None,
        },
    )


@router.post(
    "/skate-spots/{spot_id}/ratings",
    response_class=HTMLResponse,
)
async def submit_rating(
    request: Request,
    spot_id: UUID,
    rating_service: Annotated[RatingService, Depends(get_rating_service)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)],
    score: Annotated[int, Form()],
    comment: Annotated[str | None, Form()] = None,
) -> HTMLResponse:
    """Create or update the current user's rating and return the refreshed snippet."""
    if current_user is None:
        summary = rating_service.get_summary(spot_id, None)
        return templates.TemplateResponse(
            "partials/rating_section.html",
            {
                "request": request,
                "spot_id": spot_id,
                "summary": summary,
                "current_user": current_user,
                "message": "Log in to rate this spot.",
            },
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    rating_data = RatingCreate(score=score, comment=comment or None)
    summary = rating_service.set_rating(spot_id, current_user.id, rating_data)

    return templates.TemplateResponse(
        "partials/rating_section.html",
        {
            "request": request,
            "spot_id": spot_id,
            "summary": summary,
            "current_user": current_user,
            "message": "Rating saved!",
        },
    )


@router.delete(
    "/skate-spots/{spot_id}/ratings",
    response_class=HTMLResponse,
)
async def delete_rating(
    request: Request,
    spot_id: UUID,
    rating_service: Annotated[RatingService, Depends(get_rating_service)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)],
) -> HTMLResponse:
    """Remove the current user's rating and return the refreshed snippet."""
    if current_user is None:
        summary = rating_service.get_summary(spot_id, None)
        return templates.TemplateResponse(
            "partials/rating_section.html",
            {
                "request": request,
                "spot_id": spot_id,
                "summary": summary,
                "current_user": current_user,
                "message": "Log in to manage your rating.",
            },
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    try:
        summary = rating_service.delete_rating(spot_id, current_user.id)
        message = "Rating removed."
    except RatingNotFoundError:
        summary = rating_service.get_summary(spot_id, current_user.id)
        message = "No rating to remove."

    return templates.TemplateResponse(
        "partials/rating_section.html",
        {
            "request": request,
            "spot_id": spot_id,
            "summary": summary,
            "current_user": current_user,
            "message": message,
        },
    )
