"""Shared utilities for frontend routers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi.templating import Jinja2Templates

from app.models.skate_spot import Difficulty, SpotType
from app.utils.filters import build_skate_spot_filters

if TYPE_CHECKING:
    from uuid import UUID

    from fastapi import Request
    from pydantic import ValidationError

    from app.db.models import UserORM
    from app.services.favorite_service import FavoriteService
    from app.services.notification_service import NotificationService

# Initialize templates
templates = Jinja2Templates(directory="templates")

# Filter fields and constants
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


# Register custom filters to Jinja2 environment
templates.env.filters["format_spot_type"] = format_spot_type
templates.env.filters["format_difficulty"] = format_difficulty


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
    """Render the notification widget HTML."""
    context = _notification_context(request, user, notification_service)
    return templates.TemplateResponse("partials/notifications_widget.html", context)
