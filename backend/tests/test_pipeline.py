"""Provider order, actual cached fallback and snapped-coordinate coalescing."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from backend.app.providers.cache import MultiTierCache
from backend.app.providers.openmeteo import OpenMeteoProvider
from backend.app.providers.pipeline import AirQualityPipeline
from backend.app.providers.waqi import WAQIProvider
from backend.tests.fixtures.providers import model_client


@pytest.mark.asyncio
async def test_waqi_model_stale_chain(monkeypatch: pytest.MonkeyPatch) -> None:
    async with model_client() as client:
        model = OpenMeteoProvider(client)
        waqi = WAQIProvider(token="")
        cache = MultiTierCache()
        monkeypatch.setattr(cache, "set_l2_supabase", AsyncMock())
        pipe = AirQualityPipeline(waqi, model, cache)
        readings = await pipe.get_latest_readings(28.6139, 77.209)
        assert readings[0].status == "modelled_live"
        original_time = readings[0].observed_at
        cache.set_l1(28.61, 77.21, readings, ttl_seconds=-1)
        monkeypatch.setattr(
            model, "get_latest_readings", AsyncMock(side_effect=RuntimeError("outage"))
        )
        stale = await pipe.get_latest_readings(28.6139, 77.209)
        assert stale[0].status == "stale"
        assert stale[0].observed_at == original_time
        assert stale[0].source == "Open-Meteo CAMS (Modelled)"


@pytest.mark.asyncio
async def test_waqi_preferred_and_coalesced(monkeypatch: pytest.MonkeyPatch) -> None:
    async with model_client() as client:
        readings = await OpenMeteoProvider(client).get_latest_readings(28.61, 77.21)
    waqi = WAQIProvider(token="test")
    calls = 0

    async def fetch(*args: float):
        nonlocal calls
        calls += 1
        await asyncio.sleep(0.01)
        return [r.model_copy(update={"status": "live", "source": "WAQI / CPCB"}) for r in readings]

    monkeypatch.setattr(waqi, "get_latest_readings", fetch)
    model = OpenMeteoProvider()
    fallback = AsyncMock(side_effect=AssertionError("WAQI succeeded"))
    monkeypatch.setattr(model, "get_latest_readings", fallback)
    cache = MultiTierCache()
    monkeypatch.setattr(cache, "set_l2_supabase", AsyncMock())
    pipe = AirQualityPipeline(waqi, model, cache)
    results = await asyncio.gather(
        *(pipe.get_latest_readings(28.611 + i * 0.0001, 77.21) for i in range(5))
    )
    assert calls == 1
    assert all(r[0].status == "live" for r in results)
    assert results[0][0].distance_km != results[4][0].distance_km
    fallback.assert_not_awaited()


@pytest.mark.asyncio
async def test_no_provider_or_cache_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    pipe = AirQualityPipeline(waqi=WAQIProvider(token=""))
    monkeypatch.setattr(
        pipe.model, "get_latest_readings", AsyncMock(side_effect=RuntimeError("outage"))
    )
    monkeypatch.setattr(pipe.cache, "get_l2_supabase", AsyncMock(return_value=None))
    with pytest.raises(RuntimeError):
        await pipe.get_latest_readings(28.61, 77.21)
