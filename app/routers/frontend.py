"""Frontend HTML endpoints for skate spots."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.dependencies import get_optional_user
from app.db.models import UserORM
from app.models.rating import RatingCreate
from app.models.skate_spot import Difficulty, SpotType
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
    }


def _is_htmx(request: Request) -> bool:
    """Detect HTMX requests using the standard header."""

    return request.headers.get("HX-Request", "").lower() == "true"


@router.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    service: Annotated[SkateSpotService, Depends(get_skate_spot_service)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Display home page with all skate spots."""

    filter_values = _extract_filter_values(request)
    filters = _build_service_filters(filter_values)
    spots = service.list_spots(filters)

    context = _spot_list_context(request, spots, current_user, filter_values)
    return templates.TemplateResponse("index.html", context)


@router.get("/skate-spots", response_class=HTMLResponse)
async def list_spots_page(
    request: Request,
    service: Annotated[SkateSpotService, Depends(get_skate_spot_service)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Display all skate spots, optionally filtered via HTMX or page loads."""

    filter_values = _extract_filter_values(request)
    filters = _build_service_filters(filter_values)
    spots = service.list_spots(filters)

    template_name = "partials/spot_list.html" if _is_htmx(request) else "index.html"
    context = _spot_list_context(request, spots, current_user, filter_values)
    return templates.TemplateResponse(template_name, context)


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
