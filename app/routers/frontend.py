"""Frontend HTML endpoints for skate spots."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID  # noqa: TCH003

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.dependencies import get_current_user, get_optional_user
from app.db.models import UserORM  # noqa: TCH001
from app.models.rating import RatingCreate
from app.models.skate_spot import Difficulty, SpotType
from app.services.favorite_service import (
    FavoriteService,
    SpotNotFoundError,
    get_favorite_service,
)
from app.services.rating_service import (
    RatingNotFoundError,
    RatingService,
    get_rating_service,
)
from app.services.skate_spot_service import (
    SkateSpotService,
    get_skate_spot_service,
)
from spots.filters import build_skate_spot_filters

router = APIRouter(tags=["frontend"])
templates = Jinja2Templates(directory="templates")

_FILTER_FIELDS = (
    "search",
    "spot_type",
    "difficulty",
    "city",
    "country",
    "is_public",
    "requires_permission",
)
_TRUE_VALUES = {"true", "1", "yes"}
_FALSE_VALUES = {"false", "0", "no"}


def _extract_filter_values(request: Request) -> dict[str, str]:
    """Return raw query string values for the supported filter fields."""

    params = request.query_params
    return {field: params.get(field, "").strip() for field in _FILTER_FIELDS}


def _coerce_enum(value: str, enum_cls):
    """Best-effort conversion from a query string value to an Enum member."""

    if not value:
        return None
    try:
        return enum_cls(value)
    except ValueError:
        return None


def _coerce_optional_bool(value: str) -> bool | None:
    """Convert optional boolean query parameters into Python booleans."""

    if not value:
        return None
    lowered = value.lower()
    if lowered in _TRUE_VALUES:
        return True
    if lowered in _FALSE_VALUES:
        return False
    return None


def _build_service_filters(filter_values: dict[str, str]):
    """Translate raw query parameters into ``SkateSpotFilters``."""

    spot_type = _coerce_enum(filter_values["spot_type"], SpotType)
    difficulty = _coerce_enum(filter_values["difficulty"], Difficulty)

    return build_skate_spot_filters(
        search=filter_values["search"] or None,
        spot_types=[spot_type] if spot_type else None,
        difficulties=[difficulty] if difficulty else None,
        city=filter_values["city"] or None,
        country=filter_values["country"] or None,
        is_public=_coerce_optional_bool(filter_values["is_public"]),
        requires_permission=_coerce_optional_bool(filter_values["requires_permission"]),
    )


def _has_active_filters(values: dict[str, str]) -> bool:
    """Return ``True`` when any filter has a non-blank value."""

    return any(value for value in values.values())


def _spot_list_context(
    request: Request,
    spots,
    current_user: UserORM | None,
    filter_values: dict[str, str],
    favorite_spot_ids: set[UUID] | None,
) -> dict[str, object]:
    """Template context shared by the full index and HTMX partial."""

    return {
        "request": request,
        "spots": spots,
        "current_user": current_user,
        "spot_types": list(SpotType),
        "difficulties": list(Difficulty),
        "filter_values": filter_values,
        "has_active_filters": _has_active_filters(filter_values),
        "favorite_spot_ids": favorite_spot_ids or set(),
    }


def _is_htmx(request: Request) -> bool:
    """Detect HTMX requests using the standard header."""

    return request.headers.get("HX-Request", "").lower() == "true"


@router.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    service: Annotated[SkateSpotService, Depends(get_skate_spot_service)],
    favorite_service: Annotated[FavoriteService, Depends(get_favorite_service)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Display home page with all skate spots."""

    filter_values = _extract_filter_values(request)
    filters = _build_service_filters(filter_values)
    spots = service.list_spots(filters)
    favorite_spot_ids = (
        favorite_service.favorite_ids_for_user(current_user.id) if current_user else set()
    )

    context = _spot_list_context(
        request,
        spots,
        current_user,
        filter_values,
        favorite_spot_ids,
    )
    return templates.TemplateResponse("index.html", context)


@router.get("/skate-spots", response_class=HTMLResponse)
async def list_spots_page(
    request: Request,
    service: Annotated[SkateSpotService, Depends(get_skate_spot_service)],
    favorite_service: Annotated[FavoriteService, Depends(get_favorite_service)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Display all skate spots, optionally filtered via HTMX or page loads."""

    filter_values = _extract_filter_values(request)
    filters = _build_service_filters(filter_values)
    spots = service.list_spots(filters)
    favorite_spot_ids = (
        favorite_service.favorite_ids_for_user(current_user.id) if current_user else set()
    )

    template_name = "partials/spot_list.html" if _is_htmx(request) else "index.html"
    context = _spot_list_context(
        request,
        spots,
        current_user,
        filter_values,
        favorite_spot_ids,
    )
    return templates.TemplateResponse(template_name, context)


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    favorite_service: Annotated[FavoriteService, Depends(get_favorite_service)],
    current_user: Annotated[UserORM, Depends(get_current_user)],
) -> HTMLResponse:
    """Display the current user's profile with their favourite spots."""

    favorite_spots = favorite_service.list_user_favorites(current_user.id)
    favorite_spot_ids = {spot.id for spot in favorite_spots}
    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "current_user": current_user,
            "favorite_spots": favorite_spots,
            "favorite_spot_ids": favorite_spot_ids,
        },
    )


@router.get("/skate-spots/new", response_class=HTMLResponse)
async def new_spot_page(
    request: Request,
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Display form to create a new skate spot."""
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(
        "spot_form.html",
        {"request": request, "spot": None, "current_user": current_user},
    )


@router.get("/skate-spots/{spot_id}/edit", response_class=HTMLResponse)
async def edit_spot_page(
    request: Request,
    spot_id: UUID,
    service: Annotated[SkateSpotService, Depends(get_skate_spot_service)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Display form to edit an existing skate spot."""
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    spot = service.get_spot(spot_id)
    if not spot:
        return RedirectResponse(url="/", status_code=303)

    # Check if user owns the spot or is admin
    if not current_user.is_admin and not service.is_owner(spot_id, current_user.id):
        return RedirectResponse(url="/", status_code=303)

    return templates.TemplateResponse(
        "spot_form.html",
        {"request": request, "spot": spot, "current_user": current_user},
    )


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

    summary = rating_service.get_summary(spot_id, current_user.id if current_user else None)
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
    "/skate-spots/{spot_id}/favorite",
    response_class=HTMLResponse,
)
async def toggle_favorite_button(
    request: Request,
    spot_id: UUID,
    favorite_service: Annotated[FavoriteService, Depends(get_favorite_service)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)],
) -> HTMLResponse:
    """Toggle the favourite state for the current user and return the button snippet."""

    if current_user is None:
        return templates.TemplateResponse(
            "partials/favorite_button.html",
            {
                "request": request,
                "spot_id": spot_id,
                "is_favorite": False,
                "current_user": None,
                "message": "Log in to save this spot.",
            },
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    try:
        favorite_status = favorite_service.toggle_favorite(spot_id, current_user.id)
    except SpotNotFoundError:
        return templates.TemplateResponse(
            "partials/favorite_button.html",
            {
                "request": request,
                "spot_id": spot_id,
                "is_favorite": False,
                "current_user": current_user,
                "message": "This skate spot is no longer available.",
            },
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return templates.TemplateResponse(
        "partials/favorite_button.html",
        {
            "request": request,
            "spot_id": spot_id,
            "is_favorite": favorite_status.is_favorite,
            "current_user": current_user,
            "message": "Added to your favourites."
            if favorite_status.is_favorite
            else "Removed from favourites.",
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


@router.get("/map", response_class=HTMLResponse)
async def map_view(
    request: Request,
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Display interactive map of all skate spots."""

    return templates.TemplateResponse(
        "map.html",
        {"request": request, "current_user": current_user},
    )


@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Display login page."""

    if current_user:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "current_user": None},
    )


@router.get("/register", response_class=HTMLResponse)
async def register_page(
    request: Request,
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Display registration page."""

    if current_user:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(
        "register.html",
        {"request": request, "current_user": None},
    )
