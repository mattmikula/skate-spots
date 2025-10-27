"""Frontend HTML endpoints for skate spots."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID  # noqa: TCH003

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app.core.dependencies import (
    get_current_user,
    get_optional_user,
    get_user_repository,
)
from app.db.models import UserORM  # noqa: TCH001
from app.models.check_in import SpotCheckInCreate, SpotCheckInStatus, SpotCheckOut
from app.models.comment import CommentCreate
from app.models.rating import RatingCreate
from app.models.session import (
    SessionCreate,
    SessionResponse,
    SessionRSVPCreate,
    SessionStatus,
)
from app.models.skate_spot import Difficulty, SpotType
from app.models.user import UserProfileUpdate
from app.repositories.user_repository import UserRepository  # noqa: TCH001
from app.services.activity_service import ActivityService, get_activity_service
from app.services.check_in_service import (
    CheckInService,
    SpotCheckInNotFoundError,
    SpotCheckInPermissionError,
    SpotCheckInSpotNotFoundError,
    get_check_in_service,
)
from app.services.comment_service import (
    CommentNotFoundError,
    CommentPermissionError,
    CommentService,
    get_comment_service,
)
from app.services.comment_service import (
    SpotNotFoundError as CommentSpotNotFoundError,
)
from app.services.favorite_service import (
    FavoriteService,
    get_favorite_service,
)
from app.services.favorite_service import (
    SpotNotFoundError as FavoriteSpotNotFoundError,
)
from app.services.notification_service import (
    NotificationService,
    get_notification_service,
)
from app.services.rating_service import (
    RatingNotFoundError,
    RatingService,
    get_rating_service,
)
from app.services.rating_service import (
    SpotNotFoundError as RatingSpotNotFoundError,
)
from app.services.session_service import (
    SessionCapacityError,
    SessionInactiveError,
    SessionNotFoundError,
    SessionPermissionError,
    SessionRSVPNotFoundError,
    SessionService,
    SessionSpotNotFoundError,
    get_session_service,
)
from app.services.skate_spot_service import SkateSpotService, get_skate_spot_service
from app.services.user_profile_service import (
    UserProfileNotFoundError,
    UserProfileService,
    get_user_profile_service,
)
from app.utils.filters import build_skate_spot_filters

router = APIRouter(tags=["frontend"])
templates = Jinja2Templates(directory="templates")


def format_spot_type(value: str | SpotType) -> str:
    """Format spot type enum to human-readable label."""
    if isinstance(value, SpotType):
        value = value.value
    return value.replace("_", " ").title()


def format_difficulty(value: str | Difficulty) -> str:
    """Format difficulty enum to human-readable label."""
    if isinstance(value, Difficulty):
        value = value.value
    return value.capitalize()


# Add custom filters to Jinja2 environment
templates.env.filters["format_spot_type"] = format_spot_type
templates.env.filters["format_difficulty"] = format_difficulty

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


def _notification_context(
    request: Request,
    user: UserORM,
    notification_service: NotificationService,
) -> dict[str, object]:
    """Build template context for the notification widget."""

    data = notification_service.list_notifications(
        str(user.id),
        include_read=True,
        limit=10,
        offset=0,
    )
    return {
        "request": request,
        "current_user": user,
        "notifications": data.notifications,
        "unread_count": data.unread_count,
        "has_more": data.has_more,
        "total": data.total,
        "limit": data.limit,
    }


def _render_notification_widget(
    request: Request,
    user: UserORM,
    notification_service: NotificationService,
):
    context = _notification_context(request, user, notification_service)
    return templates.TemplateResponse("partials/notifications_widget.html", context)


def _comment_context(
    request: Request,
    spot_id: UUID,
    comments,
    current_user: UserORM | None,
    *,
    message: str | None = None,
    error: str | None = None,
):
    """Shared template context builder for comment partial responses."""

    return {
        "request": request,
        "spot_id": spot_id,
        "comments": comments,
        "current_user": current_user,
        "message": message,
        "error": error,
    }


def _get_session_service_with_activity(
    session_service: Annotated[SessionService, Depends(get_session_service)],
    activity_service: Annotated[ActivityService, Depends(get_activity_service)],
) -> SessionService:
    """Provide session service with activity service injected."""
    session_service.set_activity_service(activity_service)
    return session_service


def _session_context(
    request: Request,
    spot_id: UUID,
    session_service: SessionService,
    current_user: UserORM | None,
    *,
    message: str | None = None,
    error: str | None = None,
    form_errors: dict[str, list[str]] | None = None,
    form_data: dict[str, str] | None = None,
):
    """Build template context for the session HTMX partial."""

    context_error = error
    try:
        sessions = session_service.list_upcoming_sessions(
            spot_id, current_user_id=str(current_user.id) if current_user else None
        )
    except SessionSpotNotFoundError:
        sessions = []
        if context_error is None:
            context_error = "This skate spot is no longer available."

    return {
        "request": request,
        "spot_id": spot_id,
        "sessions": sessions,
        "current_user": current_user,
        "message": message,
        "error": context_error,
        "form_errors": form_errors or {},
        "form_data": form_data or {},
        "SessionResponse": SessionResponse,
        "SessionStatus": SessionStatus,
    }


def _check_in_context(
    request: Request,
    spot_id: UUID,
    check_in_service: CheckInService,
    current_user: UserORM | None,
    *,
    message: str | None = None,
    error: str | None = None,
):
    """Build template context for the check-in widget."""

    current_check_in = None
    context_error = error
    try:
        active_check_ins = check_in_service.list_active(spot_id)
        if current_user:
            current_check_in = check_in_service.get_active_for_user(spot_id, current_user.id)
    except SpotCheckInSpotNotFoundError:
        active_check_ins = []
        if context_error is None:
            context_error = "This skate spot could not be found."

    return {
        "request": request,
        "spot_id": spot_id,
        "active_check_ins": active_check_ins,
        "current_check_in": current_check_in,
        "current_user": current_user,
        "message": message,
        "error": context_error,
    }


def _session_form_payload(form) -> tuple[dict[str, object], dict[str, str]]:
    """Extract the payload and redisplay data for the session create form."""

    fields = [
        "title",
        "description",
        "start_time",
        "end_time",
        "meet_location",
        "skill_level",
        "capacity",
    ]
    form_data = {field: (form.get(field) or "").strip() for field in fields}
    payload: dict[str, object] = {
        "title": form_data["title"],
        "description": form_data["description"] or None,
        "start_time": form_data["start_time"],
        "end_time": form_data["end_time"],
        "meet_location": form_data["meet_location"] or None,
        "skill_level": form_data["skill_level"] or None,
        "capacity": form_data["capacity"] or None,
    }
    if not form_data["capacity"]:
        payload["capacity"] = None
    return payload, form_data


@router.get("/notifications/widget", response_class=HTMLResponse)
async def notifications_widget(
    request: Request,
    current_user: Annotated[UserORM | None, Depends(get_optional_user)],
    notification_service: Annotated[NotificationService, Depends(get_notification_service)],
) -> HTMLResponse:
    """Return the notification widget for the navigation bar."""

    if current_user is None:
        return HTMLResponse('<div id="notification-widget"></div>')

    return _render_notification_widget(request, current_user, notification_service)


@router.post("/notifications/mark-all", response_class=HTMLResponse)
async def notifications_mark_all(
    request: Request,
    current_user: Annotated[UserORM, Depends(get_current_user)],
    notification_service: Annotated[NotificationService, Depends(get_notification_service)],
) -> HTMLResponse:
    """Handle mark-all-read actions from the widget."""

    notification_service.mark_all_as_read(str(current_user.id))
    return _render_notification_widget(request, current_user, notification_service)


@router.post("/notifications/{notification_id}/read", response_class=HTMLResponse)
async def notifications_mark_read(
    request: Request,
    notification_id: UUID,
    current_user: Annotated[UserORM, Depends(get_current_user)],
    notification_service: Annotated[NotificationService, Depends(get_notification_service)],
) -> HTMLResponse:
    """Mark a single notification as read and refresh the widget."""

    notification_service.mark_as_read(str(notification_id), str(current_user.id))
    return _render_notification_widget(request, current_user, notification_service)


def _format_validation_errors(error: ValidationError) -> dict[str, list[str]]:
    """Group Pydantic validation errors by field for template rendering."""

    grouped: dict[str, list[str]] = {}
    for entry in error.errors():
        location = entry.get("loc", [])
        field = str(location[-1]) if location else "__all__"
        grouped.setdefault(field, []).append(entry.get("msg", "Invalid value"))
    return grouped


def _profile_page_context(
    request: Request,
    favorite_service: FavoriteService,
    current_user: UserORM,
    *,
    message: str | None = None,
    errors: dict[str, list[str]] | None = None,
    form_data: dict[str, str] | None = None,
):
    """Compose template context for the private profile page."""

    favorite_spots = favorite_service.list_user_favorites(current_user.id)
    favorite_spot_ids = {spot.id for spot in favorite_spots}

    return {
        "request": request,
        "current_user": current_user,
        "favorite_spots": favorite_spots,
        "favorite_spot_ids": favorite_spot_ids,
        "profile_message": message,
        "profile_form_errors": errors or {},
        "profile_form_data": form_data or {},
    }


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


@router.get("/nearby", response_class=HTMLResponse)
async def nearby_spots_page(
    request: Request,
    service: Annotated[SkateSpotService, Depends(get_skate_spot_service)],
    favorite_service: Annotated[FavoriteService, Depends(get_favorite_service)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Display nearby skate spots based on latitude/longitude parameters."""

    # Extract location and filter parameters
    latitude_str = request.query_params.get("latitude", "").strip()
    longitude_str = request.query_params.get("longitude", "").strip()
    radius_km_str = request.query_params.get("radius_km", "5").strip()

    # If no location provided, show the location input form
    if not latitude_str or not longitude_str:
        context = {
            "request": request,
            "current_user": current_user,
            "spot_types": list(SpotType),
            "difficulties": list(Difficulty),
        }
        return templates.TemplateResponse("nearby.html", context)

    # Parse coordinates and radius
    try:
        latitude = float(latitude_str)
        longitude = float(longitude_str)
        radius_km = float(radius_km_str)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid coordinates or radius",
        ) from exc

    # Extract additional filters
    filter_values = _extract_filter_values(request)
    spot_type = _coerce_enum(filter_values["spot_type"], SpotType)
    difficulty = _coerce_enum(filter_values["difficulty"], Difficulty)

    filters = build_skate_spot_filters(
        search=filter_values["search"] or None,
        spot_types=[spot_type] if spot_type else None,
        difficulties=[difficulty] if difficulty else None,
        city=filter_values["city"] or None,
        country=filter_values["country"] or None,
        is_public=_coerce_optional_bool(filter_values["is_public"]),
        requires_permission=_coerce_optional_bool(filter_values["requires_permission"]),
    )

    # Get nearby spots
    try:
        spots = service.get_nearby_spots(latitude, longitude, radius_km, filters)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    favorite_spot_ids = (
        favorite_service.favorite_ids_for_user(current_user.id) if current_user else set()
    )

    template_name = "partials/nearby_spot_list.html" if _is_htmx(request) else "nearby.html"
    context = {
        "request": request,
        "spots": spots,
        "current_user": current_user,
        "spot_types": list(SpotType),
        "difficulties": list(Difficulty),
        "filter_values": filter_values,
        "has_active_filters": _has_active_filters(filter_values),
        "favorite_spot_ids": favorite_spot_ids or set(),
        "latitude": latitude,
        "longitude": longitude,
        "radius_km": radius_km,
    }
    return templates.TemplateResponse(template_name, context)


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


@router.get("/skate-spots/{spot_id}", response_class=HTMLResponse)
async def spot_detail_page(
    request: Request,
    spot_id: UUID,
    service: Annotated[SkateSpotService, Depends(get_skate_spot_service)],
    favorite_service: Annotated[FavoriteService, Depends(get_favorite_service)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Display detailed view of a single skate spot."""
    spot = service.get_spot(spot_id)
    if not spot:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "title": "Spot not found",
                "message": "The requested skate spot could not be found.",
                "current_user": current_user,
            },
            status_code=status.HTTP_404_NOT_FOUND,
        )

    favorite_spot_ids = (
        favorite_service.favorite_ids_for_user(current_user.id) if current_user else set()
    )

    is_owner = False
    if current_user:
        is_owner = service.is_owner(spot_id, current_user.id)

    return templates.TemplateResponse(
        "spot_detail.html",
        {
            "request": request,
            "spot": spot,
            "current_user": current_user,
            "favorite_spot_ids": favorite_spot_ids,
            "is_owner": is_owner,
        },
    )


@router.get(
    "/skate-spots/{spot_id}/check-ins-section",
    response_class=HTMLResponse,
)
async def check_in_section(
    request: Request,
    spot_id: UUID,
    check_in_service: Annotated[CheckInService, Depends(get_check_in_service)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Render the check-in widget partial for a spot."""

    context = _check_in_context(request, spot_id, check_in_service, current_user)
    return templates.TemplateResponse("partials/spot_check_ins.html", context)


@router.post(
    "/skate-spots/{spot_id}/check-ins",
    response_class=HTMLResponse,
)
async def submit_check_in(
    request: Request,
    spot_id: UUID,
    check_in_service: Annotated[CheckInService, Depends(get_check_in_service)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Handle HTMX submissions for creating or refreshing a check-in."""

    if current_user is None:
        context = _check_in_context(
            request,
            spot_id,
            check_in_service,
            current_user,
            error="You need to log in to share a check-in.",
        )
        return templates.TemplateResponse(
            "partials/spot_check_ins.html",
            context,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    form = await request.form()
    status_value = (form.get("status") or SpotCheckInStatus.ARRIVED.value).strip().lower()
    message = form.get("message")
    ttl_raw = form.get("ttl_minutes")
    ttl_minutes = None
    if ttl_raw:
        try:
            ttl_minutes = int(ttl_raw)
        except ValueError:
            ttl_minutes = None

    try:
        payload = SpotCheckInCreate(
            status=SpotCheckInStatus(status_value),
            message=message,
            ttl_minutes=ttl_minutes,
        )
        check_in_service.check_in(spot_id, current_user, payload)
        status_label = (
            "at the spot" if payload.status is SpotCheckInStatus.ARRIVED else "heading over"
        )
        success_message = f"Shared that you're {status_label}."
        context = _check_in_context(
            request,
            spot_id,
            check_in_service,
            current_user,
            message=success_message,
        )
        return templates.TemplateResponse("partials/spot_check_ins.html", context)
    except (ValueError, ValidationError):
        context = _check_in_context(
            request,
            spot_id,
            check_in_service,
            current_user,
            error="Please choose a valid status.",
        )
        return templates.TemplateResponse(
            "partials/spot_check_ins.html",
            context,
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except SpotCheckInSpotNotFoundError as exc:
        context = _check_in_context(
            request,
            spot_id,
            check_in_service,
            current_user,
            error=str(exc),
        )
        return templates.TemplateResponse(
            "partials/spot_check_ins.html",
            context,
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except (SpotCheckInNotFoundError, SpotCheckInPermissionError):
        context = _check_in_context(
            request,
            spot_id,
            check_in_service,
            current_user,
            error="Unable to record your check-in right now.",
        )
        return templates.TemplateResponse(
            "partials/spot_check_ins.html",
            context,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


@router.post(
    "/skate-spots/{spot_id}/check-ins/{check_in_id}/checkout",
    response_class=HTMLResponse,
)
async def checkout_check_in(
    request: Request,
    spot_id: UUID,
    check_in_id: UUID,
    check_in_service: Annotated[CheckInService, Depends(get_check_in_service)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Handle HTMX submissions for ending a check-in."""

    if current_user is None:
        return HTMLResponse(status_code=status.HTTP_401_UNAUTHORIZED, content="")

    form = await request.form()
    message = form.get("message")

    try:
        payload = SpotCheckOut(message=message)
    except ValidationError:
        payload = SpotCheckOut(message=None)

    try:
        check_in_service.check_out(check_in_id, current_user, payload)
        context = _check_in_context(
            request,
            spot_id,
            check_in_service,
            current_user,
            message="Checked out successfully.",
        )
        return templates.TemplateResponse("partials/spot_check_ins.html", context)
    except SpotCheckInNotFoundError:
        return HTMLResponse(status_code=status.HTTP_404_NOT_FOUND, content="")
    except SpotCheckInPermissionError as exc:
        context = _check_in_context(
            request,
            spot_id,
            check_in_service,
            current_user,
            error=str(exc),
        )
        return templates.TemplateResponse(
            "partials/spot_check_ins.html",
            context,
            status_code=status.HTTP_403_FORBIDDEN,
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
    "/skate-spots/{spot_id}/sessions-section",
    response_class=HTMLResponse,
)
async def session_section(
    request: Request,
    spot_id: UUID,
    session_service: Annotated[SessionService, Depends(_get_session_service_with_activity)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Render the session list and form snippet for a skate spot."""

    context = _session_context(request, spot_id, session_service, current_user)
    return templates.TemplateResponse("partials/session_list.html", context)


@router.get(
    "/skate-spots/{spot_id}/sessions/{session_id}",
    response_class=HTMLResponse,
)
async def session_detail(
    request: Request,
    spot_id: UUID,
    session_id: UUID,
    skate_spot_service: Annotated[SkateSpotService, Depends(get_skate_spot_service)],
    session_service: Annotated[SessionService, Depends(_get_session_service_with_activity)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Display a single session detail page."""

    try:
        spot = skate_spot_service.get_spot(spot_id)
        if spot is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spot not found")
    except HTTPException:
        raise

    try:
        session = session_service.get_session(
            session_id, current_user_id=str(current_user.id) if current_user else None
        )
    except SessionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        ) from exc

    return templates.TemplateResponse(
        "session_detail.html",
        {
            "request": request,
            "spot": spot,
            "session": session,
            "current_user": current_user,
            "SessionResponse": SessionResponse,
            "SessionStatus": SessionStatus,
        },
    )


@router.post(
    "/skate-spots/{spot_id}/sessions",
    response_class=HTMLResponse,
)
async def create_session_partial(
    request: Request,
    spot_id: UUID,
    session_service: Annotated[SessionService, Depends(_get_session_service_with_activity)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Handle creation of a new session via HTMX."""

    if current_user is None:
        context = _session_context(
            request,
            spot_id,
            session_service,
            current_user,
            error="Log in to organise a session.",
        )
        return templates.TemplateResponse(
            "partials/session_list.html",
            context,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    form = await request.form()
    payload_dict, redisplay = _session_form_payload(form)

    try:
        payload = SessionCreate(**payload_dict)
    except ValidationError as error:
        context = _session_context(
            request,
            spot_id,
            session_service,
            current_user,
            form_errors=_format_validation_errors(error),
            form_data=redisplay,
        )
        return templates.TemplateResponse(
            "partials/session_list.html",
            context,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    try:
        session_service.create_session(spot_id, current_user, payload)
    except SessionSpotNotFoundError as exc:
        context = _session_context(
            request,
            spot_id,
            session_service,
            current_user,
            error=str(exc),
            form_data=redisplay,
        )
        return templates.TemplateResponse(
            "partials/session_list.html",
            context,
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except SessionPermissionError as exc:
        context = _session_context(
            request,
            spot_id,
            session_service,
            current_user,
            error=str(exc),
            form_data=redisplay,
        )
        return templates.TemplateResponse(
            "partials/session_list.html",
            context,
            status_code=status.HTTP_403_FORBIDDEN,
        )
    except ValueError as exc:
        context = _session_context(
            request,
            spot_id,
            session_service,
            current_user,
            error=str(exc),
            form_data=redisplay,
        )
        return templates.TemplateResponse(
            "partials/session_list.html",
            context,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    context = _session_context(
        request,
        spot_id,
        session_service,
        current_user,
        message="Session scheduled!",
    )
    return templates.TemplateResponse(
        "partials/session_list.html",
        context,
        status_code=status.HTTP_201_CREATED,
    )


@router.post(
    "/skate-spots/{spot_id}/sessions/{session_id}/rsvp",
    response_class=HTMLResponse,
)
async def submit_session_rsvp(
    request: Request,
    spot_id: UUID,
    session_id: UUID,
    session_service: Annotated[SessionService, Depends(_get_session_service_with_activity)],
    response_choice: Annotated[str, Form()],
    note: Annotated[str | None, Form()] = None,
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Create or update an RSVP via HTMX."""

    if current_user is None:
        context = _session_context(
            request,
            spot_id,
            session_service,
            current_user,
            error="Log in to RSVP.",
        )
        return templates.TemplateResponse(
            "partials/session_list.html",
            context,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    try:
        response_value = SessionResponse(response_choice)
    except ValueError:
        context = _session_context(
            request,
            spot_id,
            session_service,
            current_user,
            error="Invalid RSVP selection.",
        )
        return templates.TemplateResponse(
            "partials/session_list.html",
            context,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    payload = SessionRSVPCreate(response=response_value, note=note)

    try:
        session_service.rsvp_session(session_id, current_user, payload)
        context = _session_context(
            request,
            spot_id,
            session_service,
            current_user,
            message="RSVP updated!",
        )
        status_code = status.HTTP_200_OK
    except SessionCapacityError as exc:
        context = _session_context(
            request,
            spot_id,
            session_service,
            current_user,
            error=str(exc),
        )
        status_code = status.HTTP_409_CONFLICT
    except SessionInactiveError as exc:
        context = _session_context(
            request,
            spot_id,
            session_service,
            current_user,
            error=str(exc),
        )
        status_code = status.HTTP_400_BAD_REQUEST
    except SessionNotFoundError as exc:
        context = _session_context(
            request,
            spot_id,
            session_service,
            current_user,
            error=str(exc),
        )
        status_code = status.HTTP_404_NOT_FOUND
    except SessionPermissionError as exc:
        context = _session_context(
            request,
            spot_id,
            session_service,
            current_user,
            error=str(exc),
        )
        status_code = status.HTTP_403_FORBIDDEN
    except SessionSpotNotFoundError as exc:
        context = _session_context(
            request,
            spot_id,
            session_service,
            current_user,
            error=str(exc),
        )
        status_code = status.HTTP_404_NOT_FOUND

    return templates.TemplateResponse(
        "partials/session_list.html",
        context,
        status_code=status_code,
    )


@router.delete(
    "/skate-spots/{spot_id}/sessions/{session_id}/rsvp",
    response_class=HTMLResponse,
)
async def withdraw_session_rsvp(
    request: Request,
    spot_id: UUID,
    session_id: UUID,
    session_service: Annotated[SessionService, Depends(_get_session_service_with_activity)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Withdraw the current user's RSVP."""

    if current_user is None:
        context = _session_context(
            request,
            spot_id,
            session_service,
            current_user,
            error="Log in to manage your RSVP.",
        )
        return templates.TemplateResponse(
            "partials/session_list.html",
            context,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    try:
        session_service.withdraw_rsvp(session_id, current_user)
        context = _session_context(
            request,
            spot_id,
            session_service,
            current_user,
            message="RSVP withdrawn.",
        )
        status_code = status.HTTP_200_OK
    except SessionRSVPNotFoundError as exc:
        context = _session_context(
            request,
            spot_id,
            session_service,
            current_user,
            error=str(exc),
        )
        status_code = status.HTTP_404_NOT_FOUND
    except (SessionNotFoundError, SessionSpotNotFoundError) as exc:
        context = _session_context(
            request,
            spot_id,
            session_service,
            current_user,
            error=str(exc),
        )
        status_code = status.HTTP_404_NOT_FOUND
    except SessionPermissionError as exc:
        context = _session_context(
            request,
            spot_id,
            session_service,
            current_user,
            error=str(exc),
        )
        status_code = status.HTTP_403_FORBIDDEN

    return templates.TemplateResponse(
        "partials/session_list.html",
        context,
        status_code=status_code,
    )


@router.post(
    "/skate-spots/{spot_id}/sessions/{session_id}/cancel",
    response_class=HTMLResponse,
)
async def cancel_session_partial(
    request: Request,
    spot_id: UUID,
    session_id: UUID,
    session_service: Annotated[SessionService, Depends(_get_session_service_with_activity)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Allow organisers or admins to cancel a session."""

    if current_user is None:
        context = _session_context(
            request,
            spot_id,
            session_service,
            current_user,
            error="Log in to manage this session.",
        )
        return templates.TemplateResponse(
            "partials/session_list.html",
            context,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    try:
        session_service.change_status(session_id, current_user, SessionStatus.CANCELLED)
        context = _session_context(
            request,
            spot_id,
            session_service,
            current_user,
            message="Session cancelled.",
        )
        status_code = status.HTTP_200_OK
    except SessionPermissionError as exc:
        context = _session_context(
            request,
            spot_id,
            session_service,
            current_user,
            error=str(exc),
        )
        status_code = status.HTTP_403_FORBIDDEN
    except (SessionNotFoundError, SessionSpotNotFoundError) as exc:
        context = _session_context(
            request,
            spot_id,
            session_service,
            current_user,
            error=str(exc),
        )
        status_code = status.HTTP_404_NOT_FOUND

    return templates.TemplateResponse(
        "partials/session_list.html",
        context,
        status_code=status_code,
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

    try:
        summary = rating_service.get_summary(spot_id, current_user.id if current_user else None)
    except RatingSpotNotFoundError:
        return templates.TemplateResponse(
            "partials/rating_section.html",
            {
                "request": request,
                "spot_id": spot_id,
                "summary": None,
                "current_user": current_user,
                "error": "This skate spot is no longer available.",
            },
            status_code=status.HTTP_404_NOT_FOUND,
        )

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
    """Toggle the favorite state for the current user and return the button snippet."""

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
    except FavoriteSpotNotFoundError:
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
            "message": "Added to your favorites."
            if favorite_status.is_favorite
            else "Removed from favorites.",
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


@router.get(
    "/skate-spots/{spot_id}/comments-section",
    response_class=HTMLResponse,
)
async def comment_section(
    request: Request,
    spot_id: UUID,
    comment_service: Annotated[CommentService, Depends(get_comment_service)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)] = None,
) -> HTMLResponse:
    """Render the comment list and form snippet for a skate spot."""

    try:
        comments = comment_service.list_comments(spot_id)
    except CommentSpotNotFoundError:
        return templates.TemplateResponse(
            "partials/comment_section.html",
            _comment_context(
                request,
                spot_id,
                [],
                current_user,
                error="This skate spot is no longer available.",
            ),
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return templates.TemplateResponse(
        "partials/comment_section.html",
        _comment_context(request, spot_id, comments, current_user),
    )


@router.post(
    "/skate-spots/{spot_id}/comments",
    response_class=HTMLResponse,
)
async def submit_comment(
    request: Request,
    spot_id: UUID,
    content: Annotated[str, Form()],
    comment_service: Annotated[CommentService, Depends(get_comment_service)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)],
) -> HTMLResponse:
    """Create a comment through the HTMX form and return the refreshed snippet."""

    if current_user is None:
        try:
            comments = comment_service.list_comments(spot_id)
        except CommentSpotNotFoundError:
            return templates.TemplateResponse(
                "partials/comment_section.html",
                _comment_context(
                    request,
                    spot_id,
                    [],
                    current_user,
                    error="This skate spot is no longer available.",
                ),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return templates.TemplateResponse(
            "partials/comment_section.html",
            _comment_context(
                request,
                spot_id,
                comments,
                current_user,
                error="Log in to join the conversation.",
            ),
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    try:
        comment_data = CommentCreate(content=content)
    except ValidationError:
        try:
            comments = comment_service.list_comments(spot_id)
        except CommentSpotNotFoundError:
            return templates.TemplateResponse(
                "partials/comment_section.html",
                _comment_context(
                    request,
                    spot_id,
                    [],
                    current_user,
                    error="This skate spot is no longer available.",
                ),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return templates.TemplateResponse(
            "partials/comment_section.html",
            _comment_context(
                request,
                spot_id,
                comments,
                current_user,
                error="Comments must be between 1 and 1000 characters.",
            ),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    try:
        comments = comment_service.add_comment(spot_id, current_user, comment_data)
    except CommentSpotNotFoundError:
        return templates.TemplateResponse(
            "partials/comment_section.html",
            _comment_context(
                request,
                spot_id,
                [],
                current_user,
                error="This skate spot is no longer available.",
            ),
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return templates.TemplateResponse(
        "partials/comment_section.html",
        _comment_context(
            request,
            spot_id,
            comments,
            current_user,
            message="Comment added!",
        ),
        status_code=status.HTTP_201_CREATED,
    )


@router.delete(
    "/skate-spots/{spot_id}/comments/{comment_id}",
    response_class=HTMLResponse,
)
async def delete_comment(
    request: Request,
    spot_id: UUID,
    comment_id: UUID,
    comment_service: Annotated[CommentService, Depends(get_comment_service)],
    current_user: Annotated[UserORM | None, Depends(get_optional_user)],
) -> HTMLResponse:
    """Delete a comment through the HTMX interface and return the refreshed snippet."""

    if current_user is None:
        try:
            comments = comment_service.list_comments(spot_id)
        except CommentSpotNotFoundError:
            return templates.TemplateResponse(
                "partials/comment_section.html",
                _comment_context(
                    request,
                    spot_id,
                    [],
                    current_user,
                    error="This skate spot is no longer available.",
                ),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return templates.TemplateResponse(
            "partials/comment_section.html",
            _comment_context(
                request,
                spot_id,
                comments,
                current_user,
                error="Log in to manage your comments.",
            ),
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    try:
        comments = comment_service.delete_comment(spot_id, comment_id, current_user)
    except CommentSpotNotFoundError:
        return templates.TemplateResponse(
            "partials/comment_section.html",
            _comment_context(
                request,
                spot_id,
                [],
                current_user,
                error="This skate spot is no longer available.",
            ),
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except CommentNotFoundError:
        try:
            comments = comment_service.list_comments(spot_id)
        except CommentSpotNotFoundError:
            return templates.TemplateResponse(
                "partials/comment_section.html",
                _comment_context(
                    request,
                    spot_id,
                    [],
                    current_user,
                    error="This skate spot is no longer available.",
                ),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return templates.TemplateResponse(
            "partials/comment_section.html",
            _comment_context(
                request,
                spot_id,
                comments,
                current_user,
                message="Comment already removed.",
            ),
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except CommentPermissionError:
        try:
            comments = comment_service.list_comments(spot_id)
        except CommentSpotNotFoundError:
            return templates.TemplateResponse(
                "partials/comment_section.html",
                _comment_context(
                    request,
                    spot_id,
                    [],
                    current_user,
                    error="This skate spot is no longer available.",
                ),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return templates.TemplateResponse(
            "partials/comment_section.html",
            _comment_context(
                request,
                spot_id,
                comments,
                current_user,
                error="You can only remove your own comments unless you are an admin.",
            ),
            status_code=status.HTTP_403_FORBIDDEN,
        )

    return templates.TemplateResponse(
        "partials/comment_section.html",
        _comment_context(
            request,
            spot_id,
            comments,
            current_user,
            message="Comment removed.",
        ),
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
