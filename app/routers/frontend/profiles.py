"""User profile routers."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import ValidationError

from app.core.dependencies import (
    get_current_user,
    get_optional_user,
    get_user_repository,
)
from app.db.models import UserORM  # noqa: TCH001
from app.models.user import UserProfileUpdate
from app.repositories.user_repository import UserRepository  # noqa: TCH001
from app.routers.frontend._shared import (
    _format_validation_errors,
    _profile_page_context,
    templates,
)
from app.services.favorite_service import (
    FavoriteService,
    get_favorite_service,
)
from app.services.user_profile_service import (
    UserProfileNotFoundError,
    UserProfileService,
    get_user_profile_service,
)

router = APIRouter(tags=["frontend"])


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    favorite_service: Annotated[FavoriteService, Depends(get_favorite_service)],
    current_user: Annotated[UserORM, Depends(get_current_user)],
) -> HTMLResponse:
    """Display the current user's profile with their favorite spots and statistics."""
    message = None
    if request.query_params.get("updated") == "1":
        message = "Profile updated successfully."

    context = _profile_page_context(
        request,
        favorite_service,
        current_user,
        message=message,
    )
    return templates.TemplateResponse("profile.html", context)


@router.post("/profile", response_class=HTMLResponse)
async def update_profile_page(
    request: Request,
    favorite_service: Annotated[FavoriteService, Depends(get_favorite_service)],
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    current_user: Annotated[UserORM, Depends(get_current_user)],
    display_name: Annotated[str | None, Form()] = None,
    bio: Annotated[str | None, Form()] = None,
    location: Annotated[str | None, Form()] = None,
    website_url: Annotated[str | None, Form()] = None,
    instagram_handle: Annotated[str | None, Form()] = None,
    profile_photo_url: Annotated[str | None, Form()] = None,
) -> Response:
    """Handle updates to the current user's editable profile fields."""
    raw_form_data = {
        "display_name": display_name,
        "bio": bio,
        "location": location,
        "website_url": website_url,
        "instagram_handle": instagram_handle,
        "profile_photo_url": profile_photo_url,
    }

    try:
        profile_update = UserProfileUpdate(**raw_form_data)
    except ValidationError as error:
        context = _profile_page_context(
            request,
            favorite_service,
            current_user,
            errors=_format_validation_errors(error),
            form_data={key: value or "" for key, value in raw_form_data.items()},
        )
        return templates.TemplateResponse(
            "profile.html",
            context,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    db_user = user_repository.get_by_id(current_user.id)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user_repository.update_profile(db_user, profile_update)
    redirect_url = request.url_for("profile_page")
    return RedirectResponse(
        url=str(redirect_url.include_query_params(updated="1")),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/users/{username}", response_class=HTMLResponse)
async def public_profile_page(
    request: Request,
    username: str,
    service: Annotated[UserProfileService, Depends(get_user_profile_service)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Render the public profile page for a user."""
    try:
        profile = service.get_profile(username)
    except UserProfileNotFoundError:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "title": "Skater not found",
                "message": "The requested skater profile could not be located.",
                "current_user": current_user,
            },
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return templates.TemplateResponse(
        "user_profile.html",
        {
            "request": request,
            "profile": profile,
            "current_user": current_user,
        },
    )
