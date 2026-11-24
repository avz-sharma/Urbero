"""Exercise geocoding network branches with deterministic provider responses."""

import asyncio
import json

import httpx
import pytest

from backend.app.providers.geocoding import GeocodingProvider


def transport_client(monkeypatch: pytest.MonkeyPatch, handler) -> None:
    original = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs),
    )


@pytest.mark.asyncio
async def test_india_filter_duplicate_and_search_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0

    def handler(request):
        nonlocal calls
        calls += 1
        return httpx.Response(
            200,
            json={
                "results": [
                    {"name": "Paris", "country_code": "FR", "latitude": 48.8, "longitude": 2.3},
                    {
                        "name": "Pune",
                        "admin1": "Maharashtra",
                        "country_code": "IN",
                        "latitude": 18.52,
                        "longitude": 73.85,
                    },
                    {"name": "Pune", "country_code": "IN", "latitude": 18.52, "longitude": 73.85},
                ]
            },
        )

    transport_client(monkeypatch, handler)
    provider = GeocodingProvider()
    assert await provider.search_locations("a") == []
    results = await provider.search_locations("Pune")
    assert len(results) == 1 and results[0].city == "Pune"
    assert await provider.search_locations(" pune ") == results
    assert calls == 1


@pytest.mark.asyncio
async def test_locality_nominatim_and_reverse_snapping(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request):
        if "geocoding-api" in request.url.host:
            return httpx.Response(200, json={"results": []})
        if request.url.path == "/search":
            assert request.url.params["countrycodes"] == "in"
            return httpx.Response(
                200,
                json=[
                    {
                        "display_name": "Shivajinagar, Pune",
                        "lat": "18.53",
                        "lon": "73.85",
                        "address": {"city": "Pune", "state": "Maharashtra"},
                    }
                ],
            )
        assert request.url.params["lat"] == "18.53"
        assert request.url.params["lon"] == "73.85"
        return httpx.Response(
            200,
            json={"address": {"suburb": "Shivajinagar", "city": "Pune", "state": "Maharashtra"}},
        )

    transport_client(monkeypatch, handler)
    provider = GeocodingProvider()
    assert (await provider.search_locations("Shivajinagar"))[0].city == "Pune"
    reverse = await provider.reverse_geocode(18.53123456, 73.85123456)
    assert reverse.label == "Shivajinagar, Pune, Maharashtra"
    assert await provider.reverse_geocode(18.531111, 73.851111) == reverse


@pytest.mark.asyncio
async def test_geocoding_outage_has_no_invented_search_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def handler(request):
        raise httpx.ConnectError("offline")

    transport_client(monkeypatch, handler)
    provider = GeocodingProvider()
    assert await provider.search_locations("Unknown locality") == []
    assert (await provider.reverse_geocode(17.12, 79.3)).label == "Current Location"


@pytest.mark.asyncio
async def test_concurrent_location_search_uses_one_upstream_call(monkeypatch: pytest.MonkeyPatch):
    calls = 0

    async def respond(request):
        nonlocal calls
        calls += 1
        await asyncio.sleep(0)
        return httpx.Response(
            200,
            json={
                "results": [
                    {"name": "Pune", "country_code": "IN", "latitude": 18.52, "longitude": 73.85},
                ]
            },
        )

    transport_client(monkeypatch, respond)
    provider = GeocodingProvider()
    first, second = await asyncio.gather(
        provider.search_locations("Pune"), provider.search_locations(" pune ")
    )
    assert first == second
    assert calls == 1


@pytest.mark.asyncio
async def test_search_warms_other_workers_without_storing_query(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("SUPABASE_URL", "https://cache.test")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-key")
    stored = {}
    upstream_calls = 0

    def respond(request):
        nonlocal upstream_calls
        if request.url.host == "cache.test":
            if request.method == "POST":
                row = json.loads(request.content)
                assert "Pune" not in row["cache_key"]
                stored[row["cache_key"]] = row["payload"]
                return httpx.Response(201)
            key = request.url.params["cache_key"].removeprefix("eq.")
            return httpx.Response(200, json=[{"payload": stored[key]}] if key in stored else [])

        upstream_calls += 1
        return httpx.Response(
            200,
            json={
                "results": [
                    {"name": "Pune", "country_code": "IN", "latitude": 18.52, "longitude": 73.85},
                ]
            },
        )

    transport_client(monkeypatch, respond)
    assert await GeocodingProvider().search_locations("Pune") == (
        await GeocodingProvider().search_locations(" pune ")
    )
    assert upstream_calls == 1
