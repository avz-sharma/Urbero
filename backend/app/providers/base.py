"""Provider interface and sensor reading contracts."""

from abc import ABC, abstractmethod
from datetime import datetime
from math import asin, cos, isfinite, radians, sin, sqrt
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from backend.app.config.constants import SENSOR_BOUNDS


class SensorReading(BaseModel):
    """Normalized real-world sensor reading with mandatory honesty metadata."""

    parameter: str
    value: float = Field(ge=0, allow_inf_nan=False)
    unit: str
    observed_at: datetime
    fetched_at: datetime
    source: str
    station: str
    distance_km: float
    status: Literal["live", "modelled_live", "stale"]
    is_reference_grade: bool | None = None
    station_latitude: float | None = None
    station_longitude: float | None = None
    conversion_note: str = (
        "Concentration supplied by provider; hourly/spot estimate, not a certified CPCB average."
    )

    @model_validator(mode="after")
    def valid_pollutant(self) -> "SensorReading":
        if self.parameter not in SENSOR_BOUNDS:
            raise ValueError("Unsupported pollutant")
        validate_concentration(self.parameter, self.value)
        if self.unit != ("mg/m³" if self.parameter == "CO" else "µg/m³"):
            raise ValueError("Pollutant unit must be normalized")
        if self.observed_at.tzinfo is None or self.fetched_at.tzinfo is None:
            raise ValueError("Reading timestamps require a timezone")
        return self


class NoStationInRangeError(ValueError):
    """Raised when no active air quality monitoring stations exist within maximum radius."""

    def __init__(self, latitude: float, longitude: float, max_radius_km: float = 25.0) -> None:
        self.latitude = latitude
        self.longitude = longitude
        self.max_radius_km = max_radius_km
        super().__init__(f"No active CPCB station found within {max_radius_km} km.")


def calculate_haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance on a mean-radius Earth (6371.0088 km)."""
    a, b = radians(lat1), radians(lat2)
    delta_lat, delta_lon = radians(lat2 - lat1), radians(lon2 - lon1)
    return (
        2
        * 6371.0088
        * asin(sqrt(min(1.0, sin(delta_lat / 2) ** 2 + cos(a) * cos(b) * sin(delta_lon / 2) ** 2)))
    )


def validate_concentration(parameter: str, value: float) -> float:
    low, high = SENSOR_BOUNDS[parameter]
    if not isfinite(value) or not low <= value <= high:
        raise ValueError("Invalid pollutant concentration")
    return value


class BaseAirQualityProvider(ABC):
    """Abstract interface for air quality data providers."""

    @abstractmethod
    async def get_latest_readings(
        self, latitude: float, longitude: float, radius_km: float = 25.0
    ) -> list[SensorReading]:
        """Fetch latest sensor readings for the nearest station."""
        raise NotImplementedError
