"""API endpoints for user follow relationships."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_current_user
from app.db.models import UserORM  # noqa: TCH001
from app.models.follow import FollowersResponse, FollowingResponse, FollowStats, IsFollowingResponse
from app.services.follow_service import (
    AlreadyFollowingError,
    FollowService,
    NotFollowingError,
    SelfFollowError,
    UserNotFoundError,
    get_follow_service,
)

router = APIRouter(prefix="/api/v1/users", tags=["follows"])


@router.post(
    "/{username}/follow",
    status_code=status.HTTP_200_OK,
    summary="Follow a user",
    responses={
        200: {"description": "Successfully followed user"},
        400: {"description": "Cannot follow yourself or already following"},
        404: {"description": "User not found"},
    },
)
async def follow_user(
    username: str,
    current_user: Annotated[UserORM, Depends(get_current_user)],
    follow_service: Annotated[FollowService, Depends(get_follow_service)],
):
    """Follow a user by username.

    Args:
        username: Username of the user to follow
        current_user: Current authenticated user
        follow_service: Follow service dependency

    Returns:
        Follow status dictionary
    """
    try:
        result = follow_service.follow_user(current_user.id, username)
        return result
    except UserNotFoundError as e:  # noqa: B904
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found",
        ) from e
    except SelfFollowError as e:  # noqa: B904
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot follow yourself",
        ) from e
    except AlreadyFollowingError as e:  # noqa: B904
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You are already following {username}",
        ) from e


@router.delete(
    "/{username}/follow",
    status_code=status.HTTP_200_OK,
    summary="Unfollow a user",
    responses={
        200: {"description": "Successfully unfollowed user"},
        404: {"description": "User not found or not following"},
    },
)
async def unfollow_user(
    username: str,
    current_user: Annotated[UserORM, Depends(get_current_user)],
    follow_service: Annotated[FollowService, Depends(get_follow_service)],
):
    """Unfollow a user by username.

    Args:
        username: Username of the user to unfollow
        current_user: Current authenticated user
        follow_service: Follow service dependency

    Returns:
        Dictionary with success message
    """
    try:
        follow_service.unfollow_user(current_user.id, username)
        return {"status": "unfollowed", "username": username}
    except UserNotFoundError as e:  # noqa: B904
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found",
        ) from e
    except NotFollowingError as e:  # noqa: B904
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You are not following {username}",
        ) from e


@router.get(
    "/me/following/{username}",
    response_model=IsFollowingResponse,
    summary="Check if following a user",
)
async def is_following(
    username: str,
    current_user: Annotated[UserORM, Depends(get_current_user)],
    follow_service: Annotated[FollowService, Depends(get_follow_service)],
) -> IsFollowingResponse:
    """Check if current user is following another user.

    Args:
        username: Username to check
        current_user: Current authenticated user
        follow_service: Follow service dependency

    Returns:
        IsFollowingResponse with boolean flag
    """
    try:
        is_following_bool = follow_service.is_following(current_user.id, username)
        return IsFollowingResponse(is_following=is_following_bool)
    except UserNotFoundError as e:  # noqa: B904
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found",
        ) from e


@router.get(
    "/{username}/followers",
    response_model=FollowersResponse,
    summary="Get user's followers",
)
async def get_followers(
    username: str,  # noqa: ARG001
    follow_service: Annotated[FollowService, Depends(get_follow_service)],  # noqa: ARG001
    limit: int = 50,  # noqa: ARG001
    offset: int = 0,  # noqa: ARG001
):
    """Get list of users following a specific user.

    Args:
        username: Username of the user
        follow_service: Follow service dependency
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        FollowersResponse with list of followers
    """
    # Would need to fetch user by username first - implementation depends on UserRepository
    # This is a simplified version that assumes user_id is available
    # In practice, you'd need to get the user_id from username first
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="This endpoint requires user lookup by username",
    )


@router.get(
    "/{username}/following",
    response_model=FollowingResponse,
    summary="Get users that a user is following",
)
async def get_following(
    username: str,  # noqa: ARG001
    follow_service: Annotated[FollowService, Depends(get_follow_service)],  # noqa: ARG001
    limit: int = 50,  # noqa: ARG001
    offset: int = 0,  # noqa: ARG001
):
    """Get list of users that a specific user is following.

    Args:
        username: Username of the user
        limit: Maximum number of results
        offset: Number of results to skip
        follow_service: Follow service dependency

    Returns:
        FollowingResponse with list of users being followed
    """
    # Would need to fetch user by username first
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="This endpoint requires user lookup by username",
    )


@router.get(
    "/{username}/follow-stats",
    response_model=FollowStats,
    summary="Get user's follow statistics",
)
async def get_follow_stats(
    username: str,  # noqa: ARG001
    follow_service: Annotated[FollowService, Depends(get_follow_service)] = None,  # noqa: ARG001
):
    """Get follower and following counts for a user.

    Args:
        username: Username of the user
        follow_service: Follow service dependency

    Returns:
        FollowStats with follower and following counts
    """
    # Would need to fetch user by username first
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="This endpoint requires user lookup by username",
    )
