"""Replay real CAMS data; assert units, history boundaries and honest fallback labels."""

import asyncio
import time
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock

import httpx
import pytest

from backend.app.providers.cache import SupabaseCache
from backend.app.providers.openmeteo import OpenMeteoProvider
from backend.tests.fixtures.providers import model_client, model_payload


@pytest.mark.asyncio
async def test_current_history_forecast_and_co_conversion(monkeypatch: pytest.MonkeyPatch):
    async with model_client() as client:
        provider = OpenMeteoProvider(client)
        parse_hours = Mock(wraps=provider._hours)
        monkeypatch.setattr(provider, "_hours", parse_hours)
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
        assert parse_hours.call_count == 1


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
        worker._cache[(28.61, 77.21)] = (expired, worker._cache[(28.61, 77.21)][1])
        assert (await worker.get_latest_readings(28.611, 77.212))[0].status == "modelled_live"
        assert store.await_count == 2


@pytest.mark.asyncio
async def test_cams_recovers_from_cached_grid_without_coordinates(monkeypatch: pytest.MonkeyPatch):
    cached = model_payload()
    del cached["latitude"]
    monkeypatch.setattr(
        SupabaseCache, "get_fresh", AsyncMock(return_value=(time.time() + 600, cached))
    )
    write = AsyncMock()
    monkeypatch.setattr(SupabaseCache, "set_fresh", write)

    async with model_client() as client:
        readings = await OpenMeteoProvider(client).get_latest_readings(28.61, 77.21)
    assert readings[0].status == "modelled_live"
    assert write.await_count == 1
    assert write.await_args.args[2]["latitude"] == model_payload()["latitude"]


@pytest.mark.asyncio
@pytest.mark.parametrize("keep_waiter", [True, False])
async def test_cams_cancelled_waiter_and_failed_fetch_can_retry(keep_waiter: bool) -> None:
    started = asyncio.Event()
    release = asyncio.Event()
    responded = asyncio.Event()
    calls = 0

    async def respond(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            started.set()
            await release.wait()
            responded.set()
            return httpx.Response(200, json={})
        return httpx.Response(200, json=model_payload())

    loop = asyncio.get_running_loop()
    previous_handler = loop.get_exception_handler()
    unhandled = []
    loop.set_exception_handler(lambda _, context: unhandled.append(context["message"]))
    try:
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            provider = OpenMeteoProvider(client)
            first = asyncio.create_task(provider.get_history(28.613, 77.211))
            await asyncio.wait_for(started.wait(), timeout=1)
            second = None
            if keep_waiter:
                second = asyncio.create_task(provider.get_history(28.611, 77.212))
                await asyncio.sleep(0)
            first.cancel()
            with pytest.raises(asyncio.CancelledError):
                await first
            release.set()
            if second is not None:
                with pytest.raises(ValueError, match="hourly data missing"):
                    await asyncio.wait_for(second, timeout=1)
            else:
                await asyncio.wait_for(responded.wait(), timeout=1)
                await asyncio.sleep(0)
            assert calls == 1
            assert unhandled == []

            assert await provider.get_history(28.613, 77.211)
            assert calls == 2
    finally:
        loop.set_exception_handler(previous_handler)
