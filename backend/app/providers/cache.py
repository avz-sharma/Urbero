"""Multi-tier caching layer: L1 in-process TTL + L2 Supabase fallback with single-flight coalescing.

Protects upstream air quality provider rate limits (60 req/min) and guarantees resilient fallback
to stale-flagged historical station readings on network failures.
"""

import asyncio
import hmac
import logging
import os
import time
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

import httpx
from pydantic import ValidationError

from backend.app.config.constants import AIR_QUALITY_CACHE_TTL_SECONDS
from backend.app.providers.base import SensorReading

logger = logging.getLogger(__name__)


class SupabaseCache:
    """Shared JSON cache for readings and namespaced, expiring provider data."""

    def __init__(self) -> None:
        self._supabase_url = os.getenv("SUPABASE_URL")
        self._supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    def _headers(self) -> dict[str, str]:
        assert self._supabase_key
        return {"apikey": self._supabase_key, "Authorization": f"Bearer {self._supabase_key}"}

    def search_key(self, query: str) -> str | None:
        if not self._supabase_key or not self._supabase_url:
            return None
        return (
            "geo:search:" + hmac.digest(self._supabase_key.encode(), query.encode(), "sha256").hex()
        )

    async def get(self, key: str) -> object:
        if not self._supabase_url or not self._supabase_key:
            return None
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(5, connect=2)) as client:
                response = await client.get(
                    f"{self._supabase_url}/rest/v1/station_cache",
                    params={"select": "payload", "cache_key": f"eq.{key}", "limit": 1},
                    headers=self._headers(),
                )
                response.raise_for_status()
                rows = response.json()
                if isinstance(rows, list) and rows and isinstance(rows[0], dict):
                    return rows[0].get("payload")
        except (httpx.HTTPError, ValueError) as error:
            logger.warning("cache_read_failed tier=l2 error_type=%s", type(error).__name__)
        return None

    async def set(self, key: str, payload: object) -> None:
        if not self._supabase_url or not self._supabase_key:
            return
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(5, connect=2)) as client:
                response = await client.post(
                    f"{self._supabase_url}/rest/v1/station_cache?on_conflict=cache_key",
                    headers={**self._headers(), "Prefer": "resolution=merge-duplicates"},
                    json={"cache_key": key, "payload": payload},
                )
                response.raise_for_status()
        except (httpx.HTTPError, ValueError) as error:
            logger.warning("cache_write_failed tier=l2 error_type=%s", type(error).__name__)

    async def get_fresh(self, key: str) -> tuple[float, dict[str, Any]] | None:
        entry = await self.get(key)
        if isinstance(entry, dict):
            expires_at = entry.get("expires_at")
            data = entry.get("data")
            if (
                isinstance(expires_at, int | float)
                and expires_at > time.time()
                and isinstance(data, dict)
            ):
                return expires_at, data
        return None

    async def set_fresh(self, key: str, expires_at: float, data: dict[str, Any]) -> None:
        await self.set(key, {"expires_at": expires_at, "data": data})


class CacheEntry:
    """In-memory cache entry with expiration timestamp."""

    def __init__(
        self, readings: list[SensorReading], ttl_seconds: int = AIR_QUALITY_CACHE_TTL_SECONDS
    ) -> None:
        self.readings = readings
        self.expires_at = time.time() + ttl_seconds
        self.cached_at = datetime.now(UTC)

    @property
    def is_expired(self) -> bool:
        return time.time() >= self.expires_at


class MultiTierCache:
    """L1 in-process cache with single-flight request coalescing and Supabase L2 fallback."""

    def __init__(self, default_ttl: int = AIR_QUALITY_CACHE_TTL_SECONDS) -> None:
        self._l1_cache: dict[str, CacheEntry] = {}
        self._default_ttl = default_ttl
        self._in_flight: dict[str, asyncio.Future[list[SensorReading]]] = {}
        self._lock = asyncio.Lock()

        self._shared = SupabaseCache()

    def _normalize_key(self, lat: float, lon: float) -> str:
        """Bucket coordinates into grid key (~1-2 km precision) to maximize cache hits."""
        return f"{lat:.2f}:{lon:.2f}"

    def get_l1(
        self, lat: float, lon: float, allow_stale: bool = False
    ) -> list[SensorReading] | None:
        """Retrieve readings from in-process L1 cache."""
        key = self._normalize_key(lat, lon)
        entry = self._l1_cache.get(key)
        if not entry:
            return None

        if entry.is_expired:
            if allow_stale:
                logger.info("cache_fallback tier=l1 status=stale")
                # Mark readings as stale while keeping original observed_at
                return [
                    r.model_copy(update={"status": "stale", "fetched_at": datetime.now(UTC)})
                    for r in entry.readings
                ]
            return None

        return entry.readings

    def set_l1(
        self, lat: float, lon: float, readings: list[SensorReading], ttl_seconds: int | None = None
    ) -> None:
        """Store readings into in-process L1 cache."""
        key = self._normalize_key(lat, lon)
        ttl = self._default_ttl if ttl_seconds is None else ttl_seconds
        self._l1_cache[key] = CacheEntry(readings, ttl)
        if len(self._l1_cache) > 512:
            self._l1_cache.pop(next(iter(self._l1_cache)))

    async def get_l2_supabase(self, lat: float, lon: float) -> list[SensorReading] | None:
        """Attempt to fetch from Supabase shared cache table if configured."""
        data = await self._shared.get(self._normalize_key(lat, lon))
        if not isinstance(data, list):
            return None
        try:
            return [
                SensorReading.model_validate(r).model_copy(
                    update={"status": "stale", "fetched_at": datetime.now(UTC)}
                )
                for r in data
            ]
        except ValidationError:
            logger.warning("cache_payload_invalid tier=l2 provider=air_quality")
            return None

    async def set_l2_supabase(self, lat: float, lon: float, readings: list[SensorReading]) -> None:
        """Persist last-known-good data for cold-worker fallback; never log payloads."""
        await self._shared.set(
            self._normalize_key(lat, lon), [r.model_dump(mode="json") for r in readings]
        )

    async def get_coalesced(
        self,
        lat: float,
        lon: float,
        fetcher: Callable[[], Awaitable[list[SensorReading]]],
    ) -> list[SensorReading]:
        """Single-flight request coalescing: prevent thundering herd on live provider."""
        key = self._normalize_key(lat, lon)

        # 1. Check valid L1 cache
        cached = self.get_l1(lat, lon, allow_stale=False)
        if cached:
            return cached

        # 2. Coordinate concurrent in-flight fetches for the same key
        async with self._lock:
            cached = self.get_l1(lat, lon, allow_stale=False)
            if cached:
                return cached

            future = self._in_flight.get(key)
            is_leader = future is None

            if is_leader:
                loop = asyncio.get_running_loop()
                future = loop.create_future()
                self._in_flight[key] = future

        if not is_leader:
            # Another request is already fetching this station; await its result
            assert future is not None
            return await asyncio.shield(future)

        # Leader executes the upstream fetch
        assert future is not None
        try:
            readings = await fetcher()
            if not readings:
                raise ValueError("Provider returned no readings")
            self.set_l1(lat, lon, readings)
            await self.set_l2_supabase(lat, lon, readings)
            if not future.done():
                future.set_result(readings)
            return readings
        except Exception as err:
            logger.warning("cache_fallback error_type=%s", type(err).__name__)
            # On fetch failure, try stale L1 or Supabase L2 fallback
            stale_l1 = self.get_l1(lat, lon, allow_stale=True)
            if stale_l1:
                if not future.done():
                    future.set_result(stale_l1)
                return stale_l1

            stale_l2 = await self.get_l2_supabase(lat, lon)
            if stale_l2:
                self.set_l1(lat, lon, stale_l2, ttl_seconds=-1)
                if not future.done():
                    future.set_result(stale_l2)
                return stale_l2

            if not future.done():
                future.set_exception(err)
                future.exception()  # Retrieve leader-only exceptions without a warning.
            raise err
        except asyncio.CancelledError:
            future.cancel()
            raise
        finally:
            async with self._lock:
                self._in_flight.pop(key, None)
