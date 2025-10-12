"""Authentication endpoints for user registration and login."""

from __future__ import annotations

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Response, status
from fastapi.responses import RedirectResponse

from app.core.config import get_settings
from app.core.dependencies import get_current_user, get_user_repository
from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from app.db import models as db_models
from app.models.user import Token, User, UserCreate, UserLogin
from app.repositories import user_repository

UserORM = db_models.UserORM
UserRepository = user_repository.UserRepository

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> User:
    """Register a new user."""
    # Check if user already exists
    if user_repo.get_by_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    if user_repo.get_by_username(user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )

    # Create user
    hashed_password = get_password_hash(user_data.password)
    db_user = user_repo.create(user_data, hashed_password)

    return User.model_validate(db_user)


@router.post("/login", response_model=Token)
async def login(
    response: Response,
    user_data: UserLogin,
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> Token:
    """Login and receive an access token."""
    settings = get_settings()

    # Get user by username
    user = user_repo.get_by_username(user_data.username)
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username},
        expires_delta=access_token_expires,
    )

    # Set the token in a httponly cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=settings.access_token_expire_minutes * 60,
        samesite="lax",
    )

    return Token(access_token=access_token)


@router.post("/logout")
async def logout(response: Response) -> dict[str, str]:
    """Logout by clearing the access token cookie."""
    response.delete_cookie(key="access_token")
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: Annotated[UserORM, Depends(get_current_user)],
) -> User:
    """Get current user information."""
    return User.model_validate(current_user)


@router.post("/login/form")
async def login_form(
    username: Annotated[str, Form(...)],
    password: Annotated[str, Form(...)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> RedirectResponse:
    """Login via form submission and redirect."""
    settings = get_settings()

    # Get user by username
    user = user_repo.get_by_username(username)
    if not user or not verify_password(password, user.hashed_password):
        # In production, redirect to login page with error message
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username},
        expires_delta=access_token_expires,
    )

    # Create redirect response
    redirect_response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

    # Set the token in a httponly cookie
    redirect_response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=settings.access_token_expire_minutes * 60,
        samesite="lax",
    )

    return redirect_response


@router.post("/register/form")
async def register_form(
    email: Annotated[str, Form(...)],
    username: Annotated[str, Form(...)],
    password: Annotated[str, Form(...)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> RedirectResponse:
    """Register via form submission and redirect."""
    settings = get_settings()

    # Check if user already exists
    if user_repo.get_by_email(email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    if user_repo.get_by_username(username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )

    # Create user
    user_data = UserCreate(email=email, username=username, password=password)
    hashed_password = get_password_hash(user_data.password)
    db_user = user_repo.create(user_data, hashed_password)

    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(db_user.id), "username": db_user.username},
        expires_delta=access_token_expires,
    )

    # Create redirect response
    redirect_response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

    # Set the token in a httponly cookie
    redirect_response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=settings.access_token_expire_minutes * 60,
        samesite="lax",
    )

    return redirect_response
