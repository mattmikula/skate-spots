"""Tests for the weather service caching behaviour."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.db.models import WeatherSnapshotORM
from app.models.skate_spot import Difficulty, Location, SkateSpotCreate, SpotType
from app.models.weather import HourlyForecast, WeatherCondition, WeatherData
from app.repositories.skate_spot_repository import SkateSpotRepository
from app.repositories.weather_repository import WeatherRepository
from app.services.weather_service import (
    WeatherService,
    WeatherSpotNotFoundError,
    WeatherUnavailableError,
)


class StubClient:
    """Deterministic provider stub."""

    def __init__(self) -> None:
        self.should_fail = False
        self.calls = 0
        now = datetime.now(UTC)
        self.payload = WeatherData(
            source="stub",
            fetched_at=now,
            current=WeatherCondition(
                observed_at=now,
                temperature_c=20.0,
                apparent_temperature_c=19.0,
                wind_speed_kph=12.0,
                precipitation_probability=30.0,
                condition_code=1,
                summary="Clear",
                icon="☀️",
            ),
            forecast=[
                HourlyForecast(
                    timestamp=now + timedelta(hours=idx + 1),
                    temperature_c=19.0 + idx,
                    precipitation_probability=10.0 * idx,
                    condition_code=1,
                    summary="Clear",
                    icon="☀️",
                )
                for idx in range(3)
            ],
        )

    def fetch(self, latitude: float, longitude: float) -> WeatherData:
        self.calls += 1
        if self.should_fail:
            raise RuntimeError("provider down")
        return self.payload


@pytest.fixture
def weather_service(session_factory):
    """Build a weather service with stubbed provider and in-memory cache DB."""

    db = session_factory()
    client = StubClient()
    repo = WeatherRepository(db)
    service = WeatherService(db, repository=repo, client=client, ttl_minutes=60)
    try:
        yield service, client, db
    finally:
        db.close()


@pytest.fixture
def spot(session_factory):
    """Persist a sample skate spot for weather tests."""

    repo = SkateSpotRepository(session_factory=session_factory)
    payload = SkateSpotCreate(
        name="Weather Test Spot",
        description="Spot for exercising weather lookups",
        spot_type=SpotType.STREET,
        difficulty=Difficulty.BEGINNER,
        location=Location(
            latitude=40.0,
            longitude=-74.0,
            address=None,
            city="Test City",
            country="Testland",
        ),
    )
    created = repo.create(payload, user_id=str(uuid4()))
    return created


def test_fetches_and_caches_weather(weather_service, spot):
    """Initial fetch hits provider and stores a snapshot."""

    service, client, db = weather_service

    result = service.get_weather_for_spot(spot.id)

    assert result.cached is False
    assert result.stale is False
    assert client.calls == 1
    stored = db.query(WeatherSnapshotORM).filter_by(spot_id=str(spot.id)).first()
    assert stored is not None


def test_returns_cached_weather_when_fresh(weather_service, spot):
    """Subsequent calls within TTL use cache."""

    service, client, _ = weather_service

    first = service.get_weather_for_spot(spot.id)
    second = service.get_weather_for_spot(spot.id)

    assert first.cached is False
    assert second.cached is True
    assert client.calls == 1


def test_serves_stale_when_provider_unavailable(weather_service, spot):
    """Falls back to stale cache when provider fails."""

    service, client, db = weather_service

    initial = service.get_weather_for_spot(spot.id)
    record = db.query(WeatherSnapshotORM).filter_by(spot_id=str(spot.id)).first()
    assert record is not None
    record.expires_at = datetime.now(UTC) - timedelta(minutes=5)
    db.commit()

    client.should_fail = True
    snapshot = service.get_weather_for_spot(spot.id)

    assert initial.cached is False
    assert snapshot.cached is True
    assert snapshot.stale is True
    assert client.calls == 2


def test_missing_spot_raises(weather_service):
    """Requests for missing spots raise an error."""

    service, _, _ = weather_service

    with pytest.raises(WeatherSpotNotFoundError):
        service.get_weather_for_spot(uuid4())


def test_provider_failure_without_cache_raises(session_factory, spot):
    """If provider fails and no cache exists, surface a service error."""

    db = session_factory()
    client = StubClient()
    client.should_fail = True
    service = WeatherService(db, repository=WeatherRepository(db), client=client, ttl_minutes=60)

    with pytest.raises(WeatherUnavailableError):
        service.get_weather_for_spot(spot.id)

    db.close()
