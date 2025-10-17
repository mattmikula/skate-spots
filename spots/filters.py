"""Helper utilities for building skate spot filter objects."""

from __future__ import annotations

from app.models.skate_spot import Difficulty, SkateSpotFilters, SpotType


def build_skate_spot_filters(
    *,
    search: str | None = None,
    spot_types: list[SpotType] | tuple[SpotType, ...] | None = None,
    difficulties: list[Difficulty] | tuple[Difficulty, ...] | None = None,
    city: str | None = None,
    country: str | None = None,
    is_public: bool | None = None,
    requires_permission: bool | None = None,
) -> SkateSpotFilters | None:
    """Return a ``SkateSpotFilters`` instance when at least one filter is provided."""

    normalised_spot_types = list(spot_types) if spot_types else None
    normalised_difficulties = list(difficulties) if difficulties else None

    filters = SkateSpotFilters(
        search=search,
        spot_types=normalised_spot_types,
        difficulties=normalised_difficulties,
        city=city,
        country=country,
        is_public=is_public,
        requires_permission=requires_permission,
    )

    return filters if filters.has_filters() else None
