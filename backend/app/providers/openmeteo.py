"""CAMS model data including archived forecasts; never ground station history.

Contract/attribution: https://open-meteo.com/en/docs/air-quality-api
past_days=3 returns archived model output. CO is µg/m³; CPCB requires mg/m³.
"""

import asyncio
import logging
import time
from datetime import UTC, datetime, timedelta, timezone
from typing import Any

import httpx

from backend.app.aqi.diurnal import HourlyMeasurement
from backend.app.config.constants import AIR_QUALITY_CACHE_TTL_SECONDS, OPEN_METEO_BASE_URL
from backend.app.planner.schemas import ModelledForecastResponse, ModelledPollutantHour
from backend.app.providers.base import (
    SensorReading,
    calculate_haversine_distance_km,
    validate_concentration,
)
from backend.app.providers.cache import SupabaseCache
from backend.app.providers.resilience import ResilientGet

logger = logging.getLogger(__name__)
MODEL_SOURCE = "Open-Meteo CAMS (Modelled)"
IST = timezone(timedelta(hours=5, minutes=30))
PARAMETERS = {"pm2_5": "PM2.5", "pm10": "PM10", "nitrogen_dioxide": "NO2", "carbon_monoxide": "CO"}


class OpenMeteoProvider:
    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client
        self._shared = SupabaseCache()
        self._resilience = ResilientGet()
        self._cache: dict[tuple[float, float], tuple[float, dict[str, Any]]] = {}
        self._tasks: dict[tuple[float, float], asyncio.Task[dict[str, Any]]] = {}

    async def _fetch(self, lat: float, lon: float) -> dict[str, Any]:
        shared_key = f"cams:{lat:.2f}:{lon:.2f}"
        if cached := await self._shared.get_fresh(shared_key):
            expires_at, cached_data = cached
            try:
                self._validate(cached_data)
            except (KeyError, ValueError, TypeError):
                logger.warning("cache_payload_invalid tier=l2 provider=cams")
            else:
                self._store(lat, lon, expires_at, cached_data)
                return cached_data

        params: dict[str, str | int | float] = {
            "latitude": lat,
            "longitude": lon,
            "hourly": ",".join(PARAMETERS),
            "timezone": "Asia/Kolkata",
            "past_days": 3,
            "forecast_days": 2,
            "domains": "cams_global",
        }
        if (configured_client := self._client) is not None:
            response = await self._resilience.request(
                lambda: configured_client.get(OPEN_METEO_BASE_URL, params=params)
            )
        else:
            async with httpx.AsyncClient(timeout=httpx.Timeout(8, connect=3)) as client:
                response = await self._resilience.request(
                    lambda: client.get(OPEN_METEO_BASE_URL, params=params)
                )
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        self._validate(data)
        expires_at = time.time() + AIR_QUALITY_CACHE_TTL_SECONDS
        self._store(lat, lon, expires_at, data)
        await self._shared.set_fresh(shared_key, expires_at, data)
        return data

    def _validate(self, data: dict[str, Any]) -> None:
        if not isinstance(data.get("hourly"), dict) or not data["hourly"].get("time"):
            raise ValueError("Open-Meteo hourly data missing")
        self._hours(data)

    def _store(self, lat: float, lon: float, expires_at: float, data: dict[str, Any]) -> None:
        self._cache[(lat, lon)] = (expires_at, data)
        if len(self._cache) > 512:
            self._cache.pop(next(iter(self._cache)))

    async def get_data(self, lat: float, lon: float) -> dict[str, Any]:
        key = (round(lat, 2), round(lon, 2))
        cached = self._cache.get(key)
        if cached and time.time() < cached[0]:
            return cached[1]
        task = self._tasks.get(key)
        if task is None:
            task = asyncio.create_task(self._fetch(*key))
            self._tasks[key] = task
            task.add_done_callback(lambda done: self._tasks.pop(key, None))
        return await asyncio.shield(task)

    def _hours(self, data: dict[str, Any]) -> list[tuple[datetime, dict[str, float]]]:
        hourly = data["hourly"]
        units = data.get("hourly_units", {})
        rows = []
        for i, raw_time in enumerate(hourly["time"]):
            observed = datetime.fromisoformat(raw_time)
            if observed.tzinfo is None:
                observed = observed.replace(tzinfo=IST)
            values = {}
            for key, parameter in PARAMETERS.items():
                items = hourly.get(key, [])
                if i >= len(items) or items[i] is None:
                    continue
                if units.get(key) not in {"μg/m³", "µg/m³"}:
                    raise ValueError("Unexpected Open-Meteo pollutant unit")
                value = float(items[i]) / (1000 if parameter == "CO" else 1)
                values[parameter] = validate_concentration(parameter, value)
            rows.append((observed, values))
        return rows

    async def get_latest_readings(self, lat: float, lon: float) -> list[SensorReading]:
        data = await self.get_data(lat, lon)
        now = datetime.now(UTC)
        rows = [
            (t, v)
            for t, v in self._hours(data)
            if timedelta(0) <= now - t <= timedelta(hours=3) and "PM2.5" in v and len(v) >= 3
        ]
        if not rows:
            raise ValueError("No current usable CAMS data")
        observed, values = max(rows, key=lambda row: row[0])
        grid_lat, grid_lon = float(data["latitude"]), float(data["longitude"])
        return [
            SensorReading(
                parameter=p,
                value=v,
                unit="mg/m³" if p == "CO" else "µg/m³",
                observed_at=observed,
                fetched_at=now,
                source=MODEL_SOURCE,
                station="CAMS global model grid (not a station)",
                status="modelled_live",
                distance_km=calculate_haversine_distance_km(lat, lon, grid_lat, grid_lon),
                station_latitude=grid_lat,
                station_longitude=grid_lon,
                conversion_note="Hourly CAMS model output, not measured station data or certified CPCB averaging. CO µg/m³ ÷ 1000 → mg/m³. Open-Meteo and Copernicus CAMS attribution: https://open-meteo.com/en/docs/air-quality-api",
            )
            for p, v in values.items()
        ]

    async def get_history(self, lat: float, lon: float) -> list[HourlyMeasurement]:
        now = datetime.now(UTC)
        return [
            HourlyMeasurement(observed_at=t.astimezone(IST), value=v["PM2.5"])
            for t, v in self._hours(await self.get_data(lat, lon))
            if timedelta(0) <= now - t <= timedelta(hours=72) and "PM2.5" in v
        ]

    async def fetch_forecast(self, latitude: float, longitude: float) -> ModelledForecastResponse:
        data = await self.get_data(latitude, longitude)
        now = datetime.now(UTC)
        forecasts = [
            ModelledPollutantHour(
                time=t.isoformat(),
                pm25_ug_m3=v["PM2.5"],
                pm10_ug_m3=v["PM10"],
                no2_ug_m3=v.get("NO2"),
                co_ug_m3=v["CO"] * 1000 if "CO" in v else None,
            )
            for t, v in self._hours(data)
            if t >= now and "PM2.5" in v and "PM10" in v
        ][:48]
        if not forecasts:
            raise ValueError("No usable CAMS forecast")
        return ModelledForecastResponse(
            latitude=latitude,
            longitude=longitude,
            timezone="Asia/Kolkata",
            hourly_forecasts=forecasts,
        )
