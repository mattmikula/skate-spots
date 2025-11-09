"""Activity feed routers."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from app.core.dependencies import get_optional_user
from app.db.models import UserORM  # noqa: TCH001
from app.routers.frontend._shared import templates
from app.services.activity_service import ActivityService, get_activity_service

router = APIRouter(tags=["frontend"])


@router.get("/feed", response_class=HTMLResponse)
async def feed_page(
    request: Request,
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Display activity feed page."""
    return templates.TemplateResponse(
        "feed.html",
        {
            "request": request,
            "current_user": current_user,
            "is_authenticated": current_user is not None,
        },
    )


@router.get("/feed/partials/personalized", response_class=HTMLResponse)
async def feed_personalized_partial(
    request: Request,
    activity_service: Annotated[ActivityService, Depends(get_activity_service)],
    limit: int = 20,
    offset: int = 0,
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Get personalized feed partial (HTMX)."""
    if not current_user:
        return HTMLResponse(status_code=401)

    feed_response = activity_service.get_personalized_feed(str(current_user.id), limit, offset)

    if not feed_response.activities:
        return templates.TemplateResponse(
            "partials/empty_feed.html",
            {"request": request, "feed_type": "personalized"},
        )

    return templates.TemplateResponse(
        "partials/activity_feed.html",
        {
            "request": request,
            "activities": feed_response.activities,
            "current_user": current_user,
            "has_more": feed_response.has_more,
            "next_offset": offset + limit,
        },
    )


@router.get("/feed/partials/public", response_class=HTMLResponse)
async def feed_public_partial(
    request: Request,
    activity_service: Annotated[ActivityService, Depends(get_activity_service)],
    limit: int = 20,
    offset: int = 0,
) -> HTMLResponse:
    """Get public feed partial (HTMX)."""
    feed_response = activity_service.get_public_feed(limit, offset)

    if not feed_response.activities:
        return templates.TemplateResponse(
            "partials/empty_feed.html",
            {"request": request, "feed_type": "public"},
        )

    return templates.TemplateResponse(
        "partials/activity_feed.html",
        {
            "request": request,
            "activities": feed_response.activities,
            "current_user": None,
            "has_more": feed_response.has_more,
            "next_offset": offset + limit,
        },
    )
