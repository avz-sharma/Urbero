"""WAQI -> labelled CAMS -> last known good cache, with no fabricated readings."""

import logging

from backend.app.providers.base import SensorReading, calculate_haversine_distance_km
from backend.app.providers.cache import MultiTierCache
from backend.app.providers.openmeteo import OpenMeteoProvider
from backend.app.providers.waqi import WAQIProvider

logger = logging.getLogger(__name__)


class AirQualityPipeline:
    def __init__(
        self,
        waqi: WAQIProvider | None = None,
        model: OpenMeteoProvider | None = None,
        cache: MultiTierCache | None = None,
    ) -> None:
        self.waqi = waqi or WAQIProvider()
        self.model = model or OpenMeteoProvider()
        self.cache = cache or MultiTierCache()

    async def get_latest_readings(self, latitude: float, longitude: float) -> list[SensorReading]:
        lat, lon = round(latitude, 2), round(longitude, 2)

        async def fetch() -> list[SensorReading]:
            try:
                return await self.waqi.get_latest_readings(lat, lon)
            except Exception as err:
                logger.warning("provider_fallback provider=waqi error_type=%s", type(err).__name__)
            return await self.model.get_latest_readings(lat, lon)

        readings = await self.cache.get_coalesced(lat, lon, fetch)
        first = readings[0]
        if (
            first.source == "WAQI / CPCB"
            and first.station_latitude is not None
            and first.station_longitude is not None
            and calculate_haversine_distance_km(
                latitude, longitude, first.station_latitude, first.station_longitude
            )
            > 25
        ):
            readings = await self.model.get_latest_readings(lat, lon)
        return [
            r.model_copy(
                update={
                    "distance_km": calculate_haversine_distance_km(
                        latitude, longitude, r.station_latitude, r.station_longitude
                    )
                }
            )
            if r.station_latitude is not None and r.station_longitude is not None
            else r.model_copy()
            for r in readings
        ]
