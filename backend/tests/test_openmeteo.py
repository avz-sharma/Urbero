"""Replay real CAMS data; assert units, history boundaries and honest fallback labels."""

import time
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import httpx
import pytest

from backend.app.providers.cache import SupabaseCache
from backend.app.providers.openmeteo import OpenMeteoProvider
from backend.tests.fixtures.providers import model_client, model_payload


@pytest.mark.asyncio
async def test_current_history_forecast_and_co_conversion():
    async with model_client() as client:
        provider = OpenMeteoProvider(client)
        readings = await provider.get_latest_readings(28.61, 77.21)
        assert readings[0].status == "modelled_live"
        assert readings[0].source == "Open-Meteo CAMS (Modelled)"
        co = next(r for r in readings if r.parameter == "CO")
        assert co.unit == "mg/m³"
        assert co.value == model_payload()["hourly"]["carbon_monoxide"][72] / 1000
        history = await provider.get_history(28.61, 77.21)
        assert 72 <= len(history) <= 73
        now = datetime.now(UTC)
        assert all(timedelta(0) <= now - h.observed_at <= timedelta(hours=72) for h in history)
        forecast = await provider.fetch_forecast(28.61, 77.21)
        assert forecast.is_modelled_forecast
        assert all(datetime.fromisoformat(h.time) >= now for h in forecast.hourly_forecasts)


@pytest.mark.asyncio
@pytest.mark.parametrize("value", [-1, 99999, float("nan")])
async def test_invalid_concentrations_rejected(value):
    payload = model_payload()
    payload["hourly"]["pm2_5"][72] = value
    response = (
        httpx.Response(200, json=payload) if value == value else httpx.Response(200, text="{}")
    )
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda _: response)) as client:
        with pytest.raises(ValueError):
            await OpenMeteoProvider(client).get_latest_readings(28.61, 77.21)


@pytest.mark.asyncio
async def test_null_pm_not_fabricated_as_zero():
    payload = model_payload()
    payload["hourly"]["pm2_5"] = [None] * 120
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda r: httpx.Response(200, json=payload))
    ) as client:
        provider = OpenMeteoProvider(client)
        assert await provider.get_history(28.61, 77.21) == []
        with pytest.raises(ValueError):
            await provider.get_latest_readings(28.61, 77.21)


@pytest.mark.asyncio
async def test_cams_shared_cache_preserves_ttl_and_skips_upstream(monkeypatch: pytest.MonkeyPatch):
    store = AsyncMock()
    monkeypatch.setattr(SupabaseCache, "get_fresh", store)
    expired, fresh = time.time() - 1, time.time() + 600
    store.side_effect = [(fresh, model_payload()), None]
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json=model_payload()))
    ) as client:
        worker = OpenMeteoProvider(client)
        assert (await worker.get_latest_readings(28.613, 77.211))[0].status == "modelled_live"
        assert worker._cache[(28.61, 77.21)][0] == fresh
        assert store.await_count == 1
        worker._cache[(28.61, 77.21)] = (expired, model_payload())
        assert (await worker.get_latest_readings(28.611, 77.212))[0].status == "modelled_live"
        assert store.await_count == 2
