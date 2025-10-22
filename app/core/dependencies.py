"""FastAPI dependencies for authentication and authorization."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import Cookie, Depends, HTTPException, status

from app.core.security import decode_access_token
from app.db import models as db_models
from app.db.database import get_db
from app.repositories import user_repository

UserRepository = user_repository.UserRepository
UserORM = db_models.UserORM


def get_user_repository(db: Annotated[Any, Depends(get_db)]) -> UserRepository:
    """Get user repository instance."""
    return UserRepository(db)


async def get_current_user(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    access_token: Annotated[str | None, Cookie()] = None,
) -> UserORM:
    """Get the current authenticated user from the access token cookie."""
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Decode the token
    payload = decode_access_token(access_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    user = user_repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    return user


async def get_current_active_user(
    current_user: Annotated[UserORM, Depends(get_current_user)],
) -> UserORM:
    """Get the current active user."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_optional_user(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    access_token: Annotated[str | None, Cookie()] = None,
) -> UserORM | None:
    """Get the current user if authenticated, otherwise return None."""
    if not access_token:
        return None

    payload = decode_access_token(access_token)
    if payload is None:
        return None

    user_id: str | None = payload.get("sub")
    if user_id is None:
        return None

    user = user_repo.get_by_id(user_id)
    if user is None or not user.is_active:
        return None

    return user
