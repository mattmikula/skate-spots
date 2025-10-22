"""API endpoints for user follow relationships."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.dependencies import get_current_user, get_user_repository
from app.db.models import UserORM  # noqa: TCH001
from app.models.follow import FollowersResponse, FollowingResponse, FollowStats, IsFollowingResponse
from app.repositories.user_repository import UserRepository  # noqa: TCH001
from app.services.follow_service import (
    AlreadyFollowingError,
    FollowService,
    NotFollowingError,
    SelfFollowError,
    UserNotFoundError,
    get_follow_service,
)

router = APIRouter(prefix="/api/v1/users", tags=["follows"])
templates = Jinja2Templates(directory="templates")


@router.post(
    "/{username}/follow",
    response_class=HTMLResponse,
    status_code=status.HTTP_200_OK,
    summary="Follow a user",
    responses={
        200: {"description": "Successfully followed user"},
        400: {"description": "Cannot follow yourself or already following"},
        404: {"description": "User not found"},
    },
)
async def follow_user(
    request: Request,
    username: str,
    current_user: Annotated[UserORM, Depends(get_current_user)],
    follow_service: Annotated[FollowService, Depends(get_follow_service)],
) -> HTMLResponse:
    """Follow a user by username.

    Args:
        request: HTTP request object
        username: Username of the user to follow
        current_user: Current authenticated user
        follow_service: Follow service dependency

    Returns:
        HTML fragment of updated follow button
    """
    try:
        follow_service.follow_user(current_user.id, username)
        return templates.TemplateResponse(
            "partials/follow_button.html",
            {
                "request": request,
                "target_username": username,
                "is_following": True,
                "current_user": current_user,
            },
        )
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
    response_class=HTMLResponse,
    status_code=status.HTTP_200_OK,
    summary="Unfollow a user",
    responses={
        200: {"description": "Successfully unfollowed user"},
        404: {"description": "User not found or not following"},
    },
)
async def unfollow_user(
    request: Request,
    username: str,
    current_user: Annotated[UserORM, Depends(get_current_user)],
    follow_service: Annotated[FollowService, Depends(get_follow_service)],
) -> HTMLResponse:
    """Unfollow a user by username.

    Args:
        request: HTTP request object
        username: Username of the user to unfollow
        current_user: Current authenticated user
        follow_service: Follow service dependency

    Returns:
        HTML fragment of updated follow button
    """
    try:
        follow_service.unfollow_user(current_user.id, username)
        return templates.TemplateResponse(
            "partials/follow_button.html",
            {
                "request": request,
                "target_username": username,
                "is_following": False,
                "current_user": current_user,
            },
        )
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
    username: str,
    follow_service: Annotated[FollowService, Depends(get_follow_service)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    limit: int = 50,
    offset: int = 0,
) -> FollowersResponse:
    """Get list of users following a specific user.

    Args:
        username: Username of the user
        follow_service: Follow service dependency
        user_repo: User repository dependency
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        FollowersResponse with list of followers
    """
    # Get user by username
    user = user_repo.get_by_username(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found",
        )

    followers, total_count = follow_service.get_followers(str(user.id), limit, offset)
    return FollowersResponse(
        followers=followers,
        total=total_count,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{username}/following",
    response_model=FollowingResponse,
    summary="Get users that a user is following",
)
async def get_following(
    username: str,
    follow_service: Annotated[FollowService, Depends(get_follow_service)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    limit: int = 50,
    offset: int = 0,
) -> FollowingResponse:
    """Get list of users that a specific user is following.

    Args:
        username: Username of the user
        follow_service: Follow service dependency
        user_repo: User repository dependency
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        FollowingResponse with list of users being followed
    """
    # Get user by username
    user = user_repo.get_by_username(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found",
        )

    following, total_count = follow_service.get_following(str(user.id), limit, offset)
    return FollowingResponse(
        following=following,
        total=total_count,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{username}/follow-stats",
    response_model=FollowStats,
    summary="Get user's follow statistics",
)
async def get_follow_stats(
    username: str,
    follow_service: Annotated[FollowService, Depends(get_follow_service)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> FollowStats:
    """Get follower and following counts for a user.

    Args:
        username: Username of the user
        follow_service: Follow service dependency
        user_repo: User repository dependency

    Returns:
        FollowStats with follower and following counts
    """
    # Get user by username
    user = user_repo.get_by_username(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found",
        )

    return follow_service.get_follow_stats(str(user.id))
