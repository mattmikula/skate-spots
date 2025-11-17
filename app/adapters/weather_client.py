"""HTTP client for retrieving weather data from Open-Meteo."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Final

import httpx

from app.core.logging import get_logger
from app.models.weather import HourlyForecast, WeatherCondition, WeatherData

OPEN_METEO_URL: Final[str] = "https://api.open-meteo.com/v1/forecast"
_DEFAULT_TIMEOUT = 6.0


class WeatherProviderError(Exception):
    """Raised when the weather provider cannot fulfil a request."""


class OpenMeteoWeatherClient:
    """Fetch and normalise weather data from Open-Meteo."""

    def __init__(
        self,
        *,
        timeout: float = _DEFAULT_TIMEOUT,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._timeout = timeout
        self._transport = transport
        self._logger = get_logger(__name__)

    def fetch(self, latitude: float, longitude: float) -> WeatherData:
        """Fetch current weather and the next 12 hours of forecast."""

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current_weather": "true",
            "hourly": "temperature_2m,apparent_temperature,precipitation_probability,weathercode",
            "forecast_days": 1,
            "timezone": "auto",
        }

        try:
            response = httpx.get(
                OPEN_METEO_URL,
                params=params,
                timeout=self._timeout,
                transport=self._transport,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:  # pragma: no cover - network level guard
            self._logger.warning(
                "weather provider request failed",
                error=str(exc),
                latitude=latitude,
                longitude=longitude,
            )
            raise WeatherProviderError("Weather provider unavailable") from exc

        payload = response.json()
        return self._parse_payload(payload)

    def _parse_payload(self, payload: dict[str, Any]) -> WeatherData:
        """Normalise an Open-Meteo response."""

        try:
            current_section = payload["current_weather"]
            hourly_section = payload["hourly"]
        except KeyError as exc:  # pragma: no cover - defensive
            raise WeatherProviderError("Weather provider returned an unexpected payload") from exc

        current_time = self._parse_timestamp(current_section.get("time"))
        current_temp = float(current_section.get("temperature"))
        weather_code = int(current_section.get("weathercode"))
        wind_kph = float(current_section.get("windspeed"))

        hourly_times = [self._parse_timestamp(ts) for ts in hourly_section.get("time", [])]
        temps = [float(value) for value in hourly_section.get("temperature_2m", [])]
        feels_like = [
            float(value) if value is not None else None
            for value in hourly_section.get("apparent_temperature", [])
        ]
        precip = [
            float(value) if value is not None else None
            for value in hourly_section.get("precipitation_probability", [])
        ]
        hourly_codes = [
            int(value) if value is not None else None
            for value in hourly_section.get("weathercode", [])
        ]

        hourly_lookup = {timestamp: idx for idx, timestamp in enumerate(hourly_times)}
        current_idx = hourly_lookup.get(current_time)

        apparent_temp = feels_like[current_idx] if current_idx is not None else None
        precip_prob = precip[current_idx] if current_idx is not None else None
        hourly_code = hourly_codes[current_idx] if current_idx is not None else weather_code

        current = WeatherCondition(
            observed_at=current_time,
            temperature_c=current_temp,
            apparent_temperature_c=apparent_temp,
            wind_speed_kph=wind_kph,
            precipitation_probability=precip_prob,
            condition_code=hourly_code,
            summary=_code_to_summary(hourly_code or weather_code),
            icon=_code_to_icon(hourly_code or weather_code),
        )

        forecast_hours: list[HourlyForecast] = []
        for idx, timestamp in enumerate(hourly_times[:12]):
            code_for_hour = None
            if idx < len(hourly_codes):
                code_for_hour = hourly_codes[idx]
            if code_for_hour is None:
                code_for_hour = weather_code

            forecast_hours.append(
                HourlyForecast(
                    timestamp=timestamp,
                    temperature_c=temps[idx] if idx < len(temps) else current_temp,
                    precipitation_probability=precip[idx] if idx < len(precip) else None,
                    condition_code=hourly_codes[idx] if idx < len(hourly_codes) else None,
                    summary=_code_to_summary(code_for_hour),
                    icon=_code_to_icon(code_for_hour),
                )
            )

        return WeatherData(
            source="open-meteo",
            fetched_at=datetime.now(UTC),
            current=current,
            forecast=forecast_hours,
        )

    @staticmethod
    def _parse_timestamp(timestamp_str: str | None) -> datetime:
        """Parse provider timestamps into aware datetimes."""

        if not timestamp_str:
            return datetime.now(UTC)
        return datetime.fromisoformat(timestamp_str).replace(tzinfo=UTC)


_WEATHER_CODE_SUMMARIES: dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Freezing rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Rain showers",
    82: "Violent rain showers",
    85: "Snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with hail",
    99: "Thunderstorm with heavy hail",
}

_WEATHER_CODE_ICONS: dict[int, str] = {
    0: "☀️",
    1: "🌤️",
    2: "⛅",
    3: "☁️",
    45: "🌫️",
    48: "❄️",
    51: "🌦️",
    53: "🌦️",
    55: "🌧️",
    56: "🌧️",
    57: "🌧️",
    61: "🌧️",
    63: "🌧️",
    65: "🌧️",
    66: "🌧️",
    67: "🌧️",
    71: "🌨️",
    73: "🌨️",
    75: "❄️",
    77: "❄️",
    80: "🌦️",
    81: "🌧️",
    82: "⛈️",
    85: "🌨️",
    86: "❄️",
    95: "⛈️",
    96: "⛈️",
    99: "⛈️",
}


def _code_to_summary(code: int | None) -> str:
    if code is None:
        return "Unknown"
    return _WEATHER_CODE_SUMMARIES.get(code, "Unknown")


def _code_to_icon(code: int | None) -> str | None:
    if code is None:
        return None
    return _WEATHER_CODE_ICONS.get(code)
