"""Tests for the Open-Meteo weather client parsing logic."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

from app.adapters.weather_client import OpenMeteoWeatherClient


def test_forecast_starts_from_current_hour():
    """Forecast hours should begin at the provider's reported current hour."""

    client = OpenMeteoWeatherClient()
    base = datetime(2025, 1, 1, tzinfo=UTC)
    hourly_times = [
        (base + timedelta(hours=idx)).replace(tzinfo=None).isoformat() for idx in range(24)
    ]
    temps = [float(idx) for idx in range(24)]

    payload = {
        "current_weather": {
            "time": hourly_times[6],
            "temperature": temps[6],
            "weathercode": 1,
            "windspeed": 12.0,
        },
        "hourly": {
            "time": hourly_times,
            "temperature_2m": temps,
            "apparent_temperature": [temp + 0.5 for temp in temps],
            "precipitation_probability": [10.0 for _ in temps],
            "weathercode": [1 for _ in temps],
        },
    }

    data = client._parse_payload(payload)

    assert len(data.forecast) == 12
    assert data.forecast[0].timestamp == base + timedelta(hours=6)
    assert data.forecast[0].temperature_c == temps[6]
    assert data.forecast[-1].timestamp == base + timedelta(hours=17)


def test_offsets_are_converted_to_utc():
    """Provider timestamps with offsets should be normalised to UTC."""

    client = OpenMeteoWeatherClient()
    offset = timezone(timedelta(hours=2))
    base = datetime(2025, 1, 1, 12, tzinfo=offset)

    payload = {
        "current_weather": {
            "time": base.isoformat(),
            "temperature": 10.0,
            "weathercode": 2,
            "windspeed": 8.0,
        },
        "hourly": {
            "time": [base.isoformat(), (base + timedelta(hours=1)).isoformat()],
            "temperature_2m": [10.0, 11.0],
            "apparent_temperature": [9.5, 10.5],
            "precipitation_probability": [20.0, 30.0],
            "weathercode": [2, 3],
        },
    }

    data = client._parse_payload(payload)

    assert data.current.observed_at.tzinfo is UTC
    assert data.current.observed_at.hour == 10
    assert data.forecast[0].timestamp.hour == 10
    assert data.forecast[1].timestamp.hour == 11
