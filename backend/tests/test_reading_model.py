"""Tests for SensorReading data contract."""

from datetime import UTC, datetime

import pytest

from backend.app.providers.base import BaseAirQualityProvider, SensorReading


def test_sensor_reading_contract() -> None:
    """Verify SensorReading model creation and fields."""
    now = datetime.now(UTC)
    reading = SensorReading(
        parameter="PM2.5",
        value=65.0,
        unit="µg/m³",
        observed_at=now,
        fetched_at=now,
        source="WAQI / CPCB",
        station="ITO, Delhi",
        distance_km=2.4,
        status="live",
        is_reference_grade=True,
    )
    assert reading.parameter == "PM2.5"
    assert reading.value == 65.0
    assert reading.status == "live"
    assert reading.is_reference_grade is True


@pytest.mark.asyncio
async def test_base_provider_abstract() -> None:
    """Verify abstract methods cannot be called without implementation."""

    class DummyProvider(BaseAirQualityProvider):
        async def get_latest_readings(
            self, latitude: float, longitude: float, radius_km: float = 25.0
        ) -> list[SensorReading]:
            return await super().get_latest_readings(latitude, longitude, radius_km)

    dummy = DummyProvider()
    with pytest.raises(NotImplementedError):
        await dummy.get_latest_readings(28.6, 77.2)
