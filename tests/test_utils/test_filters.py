"""Tests for the shared skate spot filter helpers."""

from __future__ import annotations

from app.models.skate_spot import Difficulty, SpotType
from app.utils.filters import build_skate_spot_filters


def test_build_filters_returns_none_when_no_values() -> None:
    """No filters provided should return ``None``."""

    assert build_skate_spot_filters() is None
    assert build_skate_spot_filters(search="   ") is None
    assert build_skate_spot_filters(spot_types=[]) is None


def test_build_filters_normalises_sequences() -> None:
    """Sequences should be converted to lists so they are JSON serialisable."""

    filters = build_skate_spot_filters(
        search="plaza",
        spot_types=(SpotType.STREET,),
        difficulties=[Difficulty.ADVANCED],
        city="Barcelona",
        country="Spain",
        is_public=True,
        requires_permission=False,
    )

    assert filters is not None
    assert filters.search == "plaza"
    assert filters.spot_types == [SpotType.STREET]
    assert filters.difficulties == [Difficulty.ADVANCED]
    assert filters.city == "Barcelona"
    assert filters.country == "Spain"
    assert filters.is_public is True
    assert filters.requires_permission is False
