"""API endpoints for user profiles."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.comment import Comment  # noqa: F401
from app.models.profile import UserProfile
from app.models.rating import Rating  # noqa: F401
from app.models.skate_spot import SkateSpot  # noqa: F401
from app.services.profile_service import (
    ProfileService,
    UserNotFoundError,
    get_profile_service,
)

# Rebuild the UserProfile model to resolve forward references
UserProfile.model_rebuild()

router = APIRouter(prefix="/profiles", tags=["profiles"])


def _handle_user_not_found(exc: UserNotFoundError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/{username}", response_model=UserProfile)
async def get_user_profile(
    username: str,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> UserProfile:
    """Get a user's public profile by username.

    Returns the user's public information, activity statistics, recent spots,
    comments, ratings, and activity feed.
    """
    try:
        return service.get_profile_by_username(username)
    except UserNotFoundError as exc:
        raise _handle_user_not_found(exc) from exc
