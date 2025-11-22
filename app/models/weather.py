"""Pydantic models for weather data."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class WeatherCondition(BaseModel):
    """Normalised weather observation."""

    observed_at: datetime = Field(description="Timestamp of the observation in UTC")
    temperature_c: float = Field(description="Air temperature in Celsius")
    apparent_temperature_c: float | None = Field(
        default=None, description="Feels-like temperature in Celsius"
    )
    wind_speed_kph: float | None = Field(default=None, description="Wind speed in km/h")
    precipitation_probability: float | None = Field(
        default=None,
        ge=0,
        le=100,
        description="Probability of precipitation in percent",
    )
    condition_code: int | None = Field(default=None, description="Provider specific code")
    summary: str = Field(description="Human readable description of conditions")
    icon: str | None = Field(default=None, description="Emoji/icon hint for UI")


class HourlyForecast(BaseModel):
    """A forecasted weather snapshot for an hour."""

    timestamp: datetime = Field(description="Hour timestamp in UTC")
    temperature_c: float = Field(description="Forecast temperature in Celsius")
    precipitation_probability: float | None = Field(
        default=None, ge=0, le=100, description="Chance of precipitation"
    )
    condition_code: int | None = Field(default=None, description="Provider specific code")
    summary: str = Field(description="Summary phrase for the forecast hour")
    icon: str | None = Field(default=None, description="Icon hint for UI")


class WeatherData(BaseModel):
    """Current conditions and near-term forecast."""

    source: Literal["open-meteo", "stub", "unknown"] = Field(
        default="open-meteo", description="Weather data provider name"
    )
    fetched_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When the provider response was fetched",
    )
    current: WeatherCondition = Field(description="Current weather conditions")
    forecast: list[HourlyForecast] = Field(
        default_factory=list,
        description="Upcoming forecast hours (most recent first)",
    )


class WeatherSnapshot(BaseModel):
    """Weather data cached for a given skate spot."""

    spot_id: UUID
    cached: bool = Field(
        default=False,
        description="Whether the response came from the cache rather than a fresh fetch",
    )
    stale: bool = Field(
        default=False,
        description="True when cached data is past its freshness window but still served",
    )
    fetched_at: datetime = Field(description="When the data was fetched")
    expires_at: datetime = Field(description="When the cached data becomes stale")
    data: WeatherData

    @property
    def age(self) -> timedelta:
        """Return the age of the fetched data."""

        return datetime.now(UTC) - self.fetched_at
