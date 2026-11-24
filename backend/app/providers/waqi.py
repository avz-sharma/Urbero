"""WAQI CPCB stations. iaqi values are indices, never raw concentrations.

Inverse values are approximate: rounding/NowCast and averaging cannot be undone.
WAQI's published 2012 PM scale is deliberately separate from CPCB calculation.
"""

import os
import re
from datetime import UTC, datetime, timedelta
from math import isfinite
from typing import Any

import httpx

from backend.app.config.constants import WAQI_PM_BREAKPOINTS
from backend.app.providers.base import (
    BaseAirQualityProvider,
    NoStationInRangeError,
    SensorReading,
    calculate_haversine_distance_km,
    validate_concentration,
)
from backend.app.providers.resilience import ResilientGet

INDIAN_AIR_AGENCY = re.compile(
    r"\b(?:cpcb|dpcc|mpcb|wbpcb|central pollution control board|"
    r"delhi pollution control committee|maharashtra pollution control board|"
    r"west bengal pollution control board)\b",
    re.IGNORECASE,
)


def invert_iaqi(parameter: str, index: float) -> float:
    """C = C_low + (I-I_low)*(C_high-C_low)/(I_high-I_low)."""
    if not isfinite(index) or not 0 <= index <= 500:
        raise ValueError("WAQI sub-index outside invertible range")
    bands = WAQI_PM_BREAKPOINTS[parameter]
    for i_low, i_high, c_low, c_high in bands:
        if i_low <= index <= i_high:
            return round(c_low + (index - i_low) * (c_high - c_low) / (i_high - i_low), 4)
    # WAQI normally supplies integer indices; reject undocumented fractional band gaps.
    raise ValueError("WAQI sub-index lies in a breakpoint gap")


class WAQIProvider(BaseAirQualityProvider):
    def __init__(self, token: str | None = None, client: httpx.AsyncClient | None = None) -> None:
        self.token = token if token is not None else os.getenv("WAQI_API_TOKEN", "")
        self._client = client
        self._resilience = ResilientGet()

    async def get_latest_readings(
        self, latitude: float, longitude: float, radius_km: float = 25.0
    ) -> list[SensorReading]:
        if not self.token:
            raise ValueError("WAQI token is not configured")
        # Only snapped coordinates leave the server; callers recompute distance for each user.
        url = f"https://api.waqi.info/feed/geo:{latitude:.2f};{longitude:.2f}/"
        if (configured_client := self._client) is not None:
            response = await self._resilience.request(
                lambda: configured_client.get(url, params={"token": self.token})
            )
        else:
            async with httpx.AsyncClient(timeout=httpx.Timeout(8, connect=3)) as client:
                response = await self._resilience.request(
                    lambda: client.get(url, params={"token": self.token})
                )
        response.raise_for_status()
        return self._parse(response.json(), latitude, longitude, min(25, radius_km))

    def _parse(
        self, payload: dict[str, Any], lat: float, lon: float, radius: float
    ) -> list[SensorReading]:
        if payload.get("status") != "ok" or not isinstance(payload.get("data"), dict):
            raise ValueError("WAQI station unavailable")
        data = payload["data"]
        attributions = data.get("attributions", [])
        if not any(INDIAN_AIR_AGENCY.search(str(attribution)) for attribution in attributions):
            raise ValueError("WAQI station lacks Indian pollution-control attribution")
        city = data["city"]
        station_lat, station_lon = map(float, city["geo"])
        if not (-90 <= station_lat <= 90 and -180 <= station_lon <= 180):
            raise ValueError("Invalid station coordinates")
        distance = calculate_haversine_distance_km(lat, lon, station_lat, station_lon)
        if distance > radius:
            raise NoStationInRangeError(lat, lon, radius)
        observed = datetime.fromisoformat(data["time"]["iso"].replace("Z", "+00:00"))
        now = datetime.now(UTC)
        if observed.tzinfo is None or not -timedelta(minutes=10) <= now - observed <= timedelta(
            hours=3
        ):
            raise ValueError("WAQI station is not current")
        readings = []
        for key, parameter in [("pm25", "PM2.5"), ("pm10", "PM10")]:
            if key not in data.get("iaqi", {}):
                continue
            index = float(data["iaqi"][key]["v"])
            value = validate_concentration(parameter, invert_iaqi(parameter, index))
            readings.append(
                SensorReading(
                    parameter=parameter,
                    value=value,
                    unit="µg/m³",
                    observed_at=observed,
                    fetched_at=now,
                    source="WAQI / CPCB",
                    station=city["name"],
                    distance_km=distance,
                    status="live",
                    is_reference_grade=None,
                    station_latitude=station_lat,
                    station_longitude=station_lon,
                    conversion_note=f"WAQI {parameter} iaqi={index}; inverse US-EPA 2012 PM scale: C=C_low+(I-I_low)*(C_high-C_low)/(I_high-I_low) → {value} µg/m³. Approximate reconstruction, averaging window unverified; not a certified CPCB AQI. https://aqicn.org/faq/2013-09-09/revised-pm25-aqi-breakpoints/",
                )
            )
        if not any(r.parameter == "PM2.5" for r in readings):
            raise ValueError("WAQI station has no usable PM2.5")
        return readings
