"""Service for retrieving and caching weather data for skate spots."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Annotated, Any
from uuid import UUID

from fastapi import Depends

from app.adapters.weather_client import OpenMeteoWeatherClient, WeatherProviderError
from app.core.config import get_settings
from app.core.dependencies import get_db
from app.core.logging import get_logger
from app.db.models import SkateSpotORM
from app.models.weather import WeatherData, WeatherSnapshot
from app.repositories.weather_repository import WeatherRepository

DEFAULT_TTL_MINUTES = 20
STALE_SERVE_MINUTES = 120


class WeatherSpotNotFoundError(Exception):
    """Raised when a requested skate spot cannot be located."""


class WeatherUnavailableError(Exception):
    """Raised when weather data cannot be produced."""


class WeatherService:
    """Coordinate provider fetches with cached storage and freshness rules."""

    def __init__(
        self,
        db_session: Any,
        repository: WeatherRepository | None = None,
        client: OpenMeteoWeatherClient | None = None,
        *,
        ttl_minutes: int = DEFAULT_TTL_MINUTES,
        stale_serve_minutes: int = STALE_SERVE_MINUTES,
    ) -> None:
        self._db = db_session
        self._repo = repository or WeatherRepository(db_session)
        self._client = client or OpenMeteoWeatherClient()
        self._ttl = timedelta(minutes=ttl_minutes)
        self._stale_window = timedelta(minutes=stale_serve_minutes)
        self._logger = get_logger(__name__)

    def get_weather_for_spot(
        self, spot_id: UUID, *, force_refresh: bool = False
    ) -> WeatherSnapshot:
        """Return fresh weather data, falling back to cached data when needed."""

        spot = self._db.get(SkateSpotORM, str(spot_id))
        if spot is None:
            raise WeatherSpotNotFoundError(f"Skate spot with id {spot_id} not found.")

        now = self._now()
        cached_record = self._repo.get_for_spot(str(spot_id))
        if cached_record:
            cached_expires_at = self._ensure_aware(cached_record.expires_at)
            if not force_refresh and cached_expires_at > now:
                return self._to_snapshot(cached_record, cached=True, stale=False)
            stale_available = cached_expires_at + self._stale_window > now
        else:
            stale_available = False

        try:
            provider_data = self._client.fetch(spot.latitude, spot.longitude)
        except WeatherProviderError as exc:
            if cached_record and stale_available:
                self._logger.warning(
                    "serving stale weather after provider failure",
                    spot_id=str(spot_id),
                    expires_at=self._ensure_aware(cached_record.expires_at).isoformat(),
                )
                return self._to_snapshot(cached_record, cached=True, stale=True)
            raise WeatherUnavailableError("Weather provider unavailable") from exc
        except Exception as exc:  # pragma: no cover - defensive
            if cached_record and stale_available:
                self._logger.warning(
                    "serving stale weather after unexpected error",
                    spot_id=str(spot_id),
                    error=str(exc),
                )
                return self._to_snapshot(cached_record, cached=True, stale=True)
            raise WeatherUnavailableError("Weather provider unavailable") from exc

        expires_at = now + self._ttl
        stored = self._repo.save_snapshot(
            spot_id=str(spot_id),
            provider=provider_data.source,
            payload=provider_data.model_dump(mode="json"),
            fetched_at=provider_data.fetched_at,
            expires_at=expires_at,
        )
        return self._to_snapshot(stored, cached=False, stale=False)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _to_snapshot(
        self,
        record,
        *,
        cached: bool,
        stale: bool,
    ) -> WeatherSnapshot:
        data = WeatherData.model_validate(record.payload)
        return WeatherSnapshot(
            spot_id=UUID(record.spot_id),
            cached=cached,
            stale=stale,
            fetched_at=record.fetched_at,
            expires_at=record.expires_at,
            data=data,
        )

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC)

    @staticmethod
    def _ensure_aware(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value


def get_weather_service(db: Annotated[Any, Depends(get_db)]) -> WeatherService:
    """Dependency-injected weather service."""

    settings = get_settings()
    return WeatherService(
        db,
        ttl_minutes=settings.weather_cache_minutes,
        stale_serve_minutes=settings.weather_stale_minutes,
    )
