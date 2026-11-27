"""Unit tests for multi-tier cache, Supabase L2 fallback, and single-flight coalescing."""

import asyncio
import time
from datetime import UTC, datetime

import httpx
import pytest

from backend.app.providers.base import SensorReading
from backend.app.providers.cache import MultiTierCache


def _make_dummy_reading(
    param: str = "PM2.5", val: float = 75.0, status: str = "live"
) -> SensorReading:
    now = datetime.now(UTC)
    return SensorReading(
        parameter=param,
        value=val,
        unit="µg/m³",
        observed_at=now,
        fetched_at=now,
        source="air quality provider v3",
        station="Bandra, Mumbai",
        distance_km=4.5,
        status="live" if status == "live" else "stale",
        is_reference_grade=True,
    )


def test_l1_cache_hit_and_ttl() -> None:
    """Test basic L1 set, get, and expiration."""
    cache = MultiTierCache(default_ttl=1)
    readings = [_make_dummy_reading()]

    cache.set_l1(19.05, 72.85, readings, ttl_seconds=1)
    retrieved = cache.get_l1(19.05, 72.85)
    assert retrieved is not None
    assert len(retrieved) == 1
    assert retrieved[0].value == 75.0

    time.sleep(1.05)
    assert cache.get_l1(19.05, 72.85, allow_stale=False) is None


def test_stale_cache_fallback() -> None:
    """Verify that expired cache returns status='stale' when allow_stale=True."""
    cache = MultiTierCache()
    original = _make_dummy_reading(param="PM2.5", val=120.0, status="live")
    cache.set_l1(28.61, 77.21, [original], ttl_seconds=-1)  # expired in past

    stale_readings = cache.get_l1(28.61, 77.21, allow_stale=True)
    assert stale_readings is not None
    assert len(stale_readings) == 1
    assert stale_readings[0].status == "stale"
    assert stale_readings[0].observed_at == original.observed_at


@pytest.mark.asyncio
async def test_single_flight_coalescing() -> None:
    """Verify that concurrent requests for the same coordinates execute fetcher exactly once."""
    cache = MultiTierCache(default_ttl=60)
    fetch_count = 0

    async def mock_slow_fetcher() -> list[SensorReading]:
        nonlocal fetch_count
        fetch_count += 1
        await asyncio.sleep(0.05)
        return [_make_dummy_reading(val=99.0)]

    tasks = [cache.get_coalesced(28.613, 77.209, mock_slow_fetcher) for _ in range(5)]
    results = await asyncio.gather(*tasks)

    assert len(results) == 5
    for r in results:
        assert r[0].value == 99.0

    assert fetch_count == 1


@pytest.mark.asyncio
async def test_coalesced_fallback_to_stale_on_fetch_failure() -> None:
    """Verify that if live fetch fails, get_coalesced falls back to stale L1."""
    cache = MultiTierCache()
    original = _make_dummy_reading(param="PM2.5", val=110.0, status="live")
    cache.set_l1(28.65, 77.31, [original], ttl_seconds=-1)  # expired

    async def failing_fetcher() -> list[SensorReading]:
        raise RuntimeError("Upstream air quality provider timeout")

    readings = await cache.get_coalesced(28.65, 77.31, failing_fetcher)
    assert len(readings) == 1
    assert readings[0].status == "stale"
    assert readings[0].value == 110.0


@pytest.mark.asyncio
async def test_cancelling_leader_during_l2_fallback_releases_follower(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    l2_read_started = asyncio.Event()
    follower_started = asyncio.Event()

    async def respond(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            l2_read_started.set()
            await asyncio.Event().wait()
        return httpx.Response(201)

    monkeypatch.setenv("SUPABASE_URL", "https://mock.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "mock-key")
    client = httpx.AsyncClient
    transport = httpx.MockTransport(respond)
    monkeypatch.setattr(
        httpx, "AsyncClient", lambda **kwargs: client(transport=transport, **kwargs)
    )
    cache = MultiTierCache()

    async def fail_to_fetch() -> list[SensorReading]:
        raise RuntimeError("upstream unavailable")

    async def fetch_after_retry() -> list[SensorReading]:
        return [_make_dummy_reading(val=69)]

    async def follow_leader() -> list[SensorReading]:
        follower_started.set()
        return await cache.get_coalesced(28.61, 77.21, fail_to_fetch)

    leader = asyncio.create_task(cache.get_coalesced(28.61, 77.21, fail_to_fetch))
    await asyncio.wait_for(l2_read_started.wait(), timeout=1)
    follower = asyncio.create_task(follow_leader())
    await asyncio.wait_for(follower_started.wait(), timeout=1)
    leader.cancel()
    with pytest.raises(asyncio.CancelledError):
        await leader
    with pytest.raises(asyncio.CancelledError):
        await asyncio.wait_for(follower, timeout=0.2)

    fresh = await cache.get_coalesced(28.61, 77.21, fetch_after_retry)
    assert fresh[0].value == 69


@pytest.mark.asyncio
async def test_supabase_l2_lookup(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test Supabase L2 cache lookup and error handling."""
    cache = MultiTierCache()
    # Case 1: unconfigured Supabase
    assert await cache.get_l2_supabase(28.5, 77.2) is None

    # Case 2: Configured Supabase with mock response
    monkeypatch.setenv("SUPABASE_URL", "https://mock.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "mock-key")
    cache = MultiTierCache()

    dummy_payload = [_make_dummy_reading(param="PM2.5", val=88.0).model_dump(mode="json")]

    class MockSupabaseClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __aenter__(self) -> "MockSupabaseClient":
            return self

        async def __aexit__(self, *args) -> None:
            pass

        async def get(self, url: str, *args, **kwargs) -> httpx.Response:
            return httpx.Response(
                200,
                json=[{"cache_key": "28.50:77.20", "payload": dummy_payload}],
                request=httpx.Request("GET", url),
            )

    monkeypatch.setattr(httpx, "AsyncClient", MockSupabaseClient)
    res = await cache.get_l2_supabase(28.5, 77.2)
    assert res is not None
    assert len(res) == 1
    assert res[0].status == "stale"
    assert res[0].value == 88.0
