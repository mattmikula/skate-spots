"""API endpoints for activity feed."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_current_user
from app.db.models import UserORM  # noqa: TCH001
from app.models.activity import ActivityFeedResponse
from app.services.activity_service import ActivityService, get_activity_service

router = APIRouter(prefix="/api/v1/feed", tags=["activity"])


@router.get(
    "",
    response_model=ActivityFeedResponse,
    summary="Get personalized activity feed",
    responses={
        200: {"description": "Personal feed from followed users"},
        401: {"description": "User must be authenticated"},
    },
)
async def get_personalized_feed(
    current_user: Annotated[UserORM, Depends(get_current_user)],
    activity_service: Annotated[ActivityService, Depends(get_activity_service)],
    limit: int = 20,
    offset: int = 0,
) -> ActivityFeedResponse:
    """Get personalized activity feed for authenticated user.

    Shows activities from users that the current user is following.

    Args:
        limit: Maximum number of activities to return (default: 20, max: 100)
        offset: Number of activities to skip for pagination (default: 0)
        current_user: Current authenticated user
        activity_service: Activity service dependency

    Returns:
        ActivityFeedResponse with personalized activities
    """
    if limit > 100:
        limit = 100

    return activity_service.get_personalized_feed(current_user.id, limit, offset)


@router.get(
    "/public",
    response_model=ActivityFeedResponse,
    summary="Get public activity feed",
)
async def get_public_feed(
    activity_service: Annotated[ActivityService, Depends(get_activity_service)],
    limit: int = 20,
    offset: int = 0,
) -> ActivityFeedResponse:
    """Get public activity feed.

    Shows all recent activities from all users.

    Args:
        limit: Maximum number of activities to return (default: 20, max: 100)
        offset: Number of activities to skip for pagination (default: 0)
        activity_service: Activity service dependency

    Returns:
        ActivityFeedResponse with public activities
    """
    if limit > 100:
        limit = 100

    return activity_service.get_public_feed(limit, offset)


@router.get(
    "/users/{username}",
    response_model=ActivityFeedResponse,
    summary="Get user's activity history",
)
async def get_user_activity() -> ActivityFeedResponse:
    """Get activity history for a specific user.

    Note: This endpoint is not yet implemented and requires user lookup by username.

    Returns:
        501 Not Implemented error
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="This endpoint requires user lookup by username",
    )
