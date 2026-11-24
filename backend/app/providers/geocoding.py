"""India-scoped Geocoding Provider with 24-hour caching and privacy-first coordinate snapping.

Provides fast locality/city searching and reverse geocoding using Open-Meteo Geocoding
and Nominatim APIs with fallbacks to verified Indian metropolitan landmarks.
"""

import asyncio
import logging
import time
from collections.abc import Callable, Coroutine
from typing import Any, TypeVar

import httpx
from pydantic import TypeAdapter, ValidationError

from backend.app.planner.schemas import LocationSearchResult, ReverseGeocodeResult
from backend.app.providers.cache import SupabaseCache
from backend.app.providers.resilience import ResilientGet

logger = logging.getLogger(__name__)
T = TypeVar("T")
SEARCH_RESULTS = TypeAdapter(list[LocationSearchResult])


async def coalesce(
    tasks: dict[str, asyncio.Task[T]], key: str, fetch: Callable[[], Coroutine[Any, Any, T]]
) -> T:
    task = tasks.get(key)
    if task is None:
        task = asyncio.create_task(fetch())
        tasks[key] = task
        task.add_done_callback(lambda completed: tasks.pop(key, None))
    return await asyncio.shield(task)


# Curated Indian localities & cities for fast, offline-resilient matching
CURATED_INDIAN_LOCATIONS: list[LocationSearchResult] = [
    LocationSearchResult(
        label="Connaught Place, Central Delhi, Delhi",
        city="Delhi",
        state="Delhi",
        lat=28.6315,
        lon=77.2167,
    ),
    LocationSearchResult(
        label="Anand Vihar, East Delhi, Delhi",
        city="Delhi",
        state="Delhi",
        lat=28.6508,
        lon=77.3152,
    ),
    LocationSearchResult(
        label="Sector 62, Noida, Uttar Pradesh",
        city="Noida",
        state="Uttar Pradesh",
        lat=28.6270,
        lon=77.3620,
    ),
    LocationSearchResult(
        label="Indirapuram, Ghaziabad, Uttar Pradesh",
        city="Ghaziabad",
        state="Uttar Pradesh",
        lat=28.6415,
        lon=77.3712,
    ),
    LocationSearchResult(
        label="Cyber City, Gurugram, Haryana",
        city="Gurugram",
        state="Haryana",
        lat=28.4950,
        lon=77.0895,
    ),
    LocationSearchResult(
        label="Andheri West, Mumbai, Maharashtra",
        city="Mumbai",
        state="Maharashtra",
        lat=19.1363,
        lon=72.8277,
    ),
    LocationSearchResult(
        label="Bandra Kurla Complex (BKC), Mumbai, Maharashtra",
        city="Mumbai",
        state="Maharashtra",
        lat=19.0657,
        lon=72.8687,
    ),
    LocationSearchResult(
        label="Salt Lake Sector V, Kolkata, West Bengal",
        city="Kolkata",
        state="West Bengal",
        lat=22.5800,
        lon=88.4373,
    ),
    LocationSearchResult(
        label="Park Street, Kolkata, West Bengal",
        city="Kolkata",
        state="West Bengal",
        lat=22.5510,
        lon=88.3524,
    ),
    LocationSearchResult(
        label="Koramangala, Bengaluru, Karnataka",
        city="Bengaluru",
        state="Karnataka",
        lat=12.9352,
        lon=77.6245,
    ),
    LocationSearchResult(
        label="Whitefield, Bengaluru, Karnataka",
        city="Bengaluru",
        state="Karnataka",
        lat=12.9698,
        lon=77.7499,
    ),
]


class GeocodingProvider:
    """Indian geocoding with 24-hour caching and privacy grid snapping."""

    def __init__(self, cache_ttl_seconds: int = 86400) -> None:
        self.cache_ttl = cache_ttl_seconds
        self._shared = SupabaseCache()
        self._openmeteo = ResilientGet()
        self._nominatim = ResilientGet()
        self._search_tasks: dict[str, asyncio.Task[list[LocationSearchResult]]] = {}
        self._reverse_tasks: dict[str, asyncio.Task[ReverseGeocodeResult]] = {}
        self._search_cache: dict[str, tuple[float, list[LocationSearchResult]]] = {}
        self._reverse_cache: dict[str, tuple[float, ReverseGeocodeResult]] = {}

    def _normalize_query_key(self, query: str) -> str:
        return query.strip().lower()

    def _snap_grid_key(self, lat: float, lon: float) -> str:
        return f"{lat:.2f}:{lon:.2f}"

    async def search_locations(self, query: str) -> list[LocationSearchResult]:
        key = self._normalize_query_key(query)
        return await coalesce(self._search_tasks, key, lambda: self._search_locations(query))

    async def _search_locations(self, query: str) -> list[LocationSearchResult]:
        """Search Indian cities and localities with 24h caching."""
        clean_query = query.strip()
        if len(clean_query) < 2:
            return []

        norm_key = self._normalize_query_key(clean_query)
        now = time.time()

        # Check L1 cache
        if norm_key in self._search_cache:
            exp, cached_res = self._search_cache[norm_key]
            if now < exp:
                return cached_res

        shared_key = self._shared.search_key(norm_key)
        if shared_key is not None and (shared := await self._shared.get_fresh(shared_key)):
            expires_at, cached_data = shared
            try:
                cached_results = SEARCH_RESULTS.validate_python(cached_data.get("results"))
            except ValidationError:
                logger.warning("cache_payload_invalid tier=l2 provider=location_search")
            else:
                self._store_search(norm_key, expires_at, cached_results)
                return cached_results

        results: list[LocationSearchResult] = []

        # 1. Check curated locations for immediate exact/substring matches
        for loc in CURATED_INDIAN_LOCATIONS:
            if (
                clean_query.lower() in loc.label.lower()
                or clean_query.lower() in loc.city.lower()
                or clean_query.lower() in loc.state.lower()
            ):
                results.append(loc)
                if len(results) >= 5:
                    break

        # 2. If curated matches are fewer than 5, query Open-Meteo Geocoding API
        if len(results) < 5:
            try:
                url = "https://geocoding-api.open-meteo.com/v1/search"
                params: dict[str, str | int] = {
                    "name": clean_query,
                    "count": 10,
                    "language": "en",
                    "format": "json",
                }
                async with httpx.AsyncClient(timeout=httpx.Timeout(5.0, connect=3.0)) as client:
                    resp = await self._openmeteo.request(lambda: client.get(url, params=params))
                    if resp.status_code == 200:
                        data: dict[str, Any] = resp.json()
                        raw_items = data.get("results", [])
                        for item in raw_items:
                            # Prioritize or filter for India (country_code == 'IN')
                            country_code = str(item.get("country_code", "")).upper()
                            if country_code == "IN":
                                name = str(item.get("name", ""))
                                admin1 = str(item.get("admin1", name))
                                lat = float(item["latitude"])
                                lon = float(item["longitude"])
                                label = f"{name}, {admin1}, India"

                                # Avoid duplicate lat/lon
                                if not any(
                                    abs(r.lat - lat) < 0.01 and abs(r.lon - lon) < 0.01
                                    for r in results
                                ):
                                    results.append(
                                        LocationSearchResult(
                                            label=label,
                                            city=name,
                                            state=admin1,
                                            lat=round(lat, 4),
                                            lon=round(lon, 4),
                                        )
                                    )
                                    if len(results) >= 5:
                                        break
            except Exception as err:
                logger.warning(f"Open-Meteo geocoding search failed: {type(err).__name__}")

        # Only curated and city/locality results can enter the shared search cache.
        can_share = bool(results)
        # 3. Fallback to Nominatim if still empty
        if not results:
            try:
                nom_url = "https://nominatim.openstreetmap.org/search"
                nom_params: dict[str, str | int] = {
                    "q": clean_query,
                    "countrycodes": "in",
                    "format": "json",
                    "limit": 5,
                    "addressdetails": 1,
                }
                headers = {"User-Agent": "Urbero-Urban-Air-Assistant/1.0 (contact@urbero.internal)"}
                async with httpx.AsyncClient(timeout=httpx.Timeout(5.0, connect=3.0)) as client:
                    resp = await self._nominatim.request(
                        lambda: client.get(nom_url, params=nom_params, headers=headers)
                    )
                    if resp.status_code == 200:
                        nom_items = resp.json()
                        for item in nom_items:
                            display_name = str(item.get("display_name", ""))
                            address = item.get("address", {})
                            city = address.get(
                                "city", address.get("town", address.get("suburb", clean_query))
                            )
                            state = address.get("state", "India")
                            lat = float(item["lat"])
                            lon = float(item["lon"])
                            results.append(
                                LocationSearchResult(
                                    label=display_name.split(",")[0] + f", {city}, {state}",
                                    city=city,
                                    state=state,
                                    lat=round(lat, 4),
                                    lon=round(lon, 4),
                                )
                            )
                            if len(results) >= 5:
                                break
            except Exception as err:
                logger.warning(f"Nominatim geocoding search failed: {type(err).__name__}")

        # Final trimming to at most 5 items and store in cache
        final_results = results[:5]
        if final_results:
            expires_at = now + self.cache_ttl
            self._store_search(norm_key, expires_at, final_results)
            if shared_key is not None and can_share:
                await self._shared.set_fresh(
                    shared_key,
                    expires_at,
                    {"results": SEARCH_RESULTS.dump_python(final_results, mode="json")},
                )
        return final_results

    def _store_search(
        self, key: str, expires_at: float, results: list[LocationSearchResult]
    ) -> None:
        self._search_cache[key] = (expires_at, results)
        if len(self._search_cache) > 512:
            self._search_cache.pop(next(iter(self._search_cache)))

    def _store_reverse(self, key: str, expires_at: float, result: ReverseGeocodeResult) -> None:
        self._reverse_cache[key] = (expires_at, result)
        if len(self._reverse_cache) > 512:
            self._reverse_cache.pop(next(iter(self._reverse_cache)))

    async def reverse_geocode(self, lat: float, lon: float) -> ReverseGeocodeResult:
        key = self._snap_grid_key(lat, lon)
        return await coalesce(self._reverse_tasks, key, lambda: self._reverse_geocode(lat, lon))

    async def _reverse_geocode(self, lat: float, lon: float) -> ReverseGeocodeResult:
        """Reverse geocode coordinates with 2-decimal snapping and 24h caching."""
        snapped_lat = round(lat, 2)
        snapped_lon = round(lon, 2)
        grid_key = self._snap_grid_key(snapped_lat, snapped_lon)
        now = time.time()

        if grid_key in self._reverse_cache:
            exp, cached_rev = self._reverse_cache[grid_key]
            if now < exp:
                return cached_rev

        # Match against known curated locations within ~5km
        for loc in CURATED_INDIAN_LOCATIONS:
            if abs(loc.lat - snapped_lat) < 0.05 and abs(loc.lon - snapped_lon) < 0.05:
                res = ReverseGeocodeResult(
                    label=loc.label,
                    city=loc.city,
                    state=loc.state,
                )
                self._store_reverse(grid_key, now + self.cache_ttl, res)
                return res

        shared_key = f"geo:reverse:{grid_key}"
        if shared := await self._shared.get_fresh(shared_key):
            expires_at, data = shared
            try:
                cached_reverse = ReverseGeocodeResult.model_validate(data)
            except ValidationError:
                logger.warning("cache_payload_invalid tier=l2 provider=reverse_geocode")
            else:
                self._store_reverse(grid_key, expires_at, cached_reverse)
                return cached_reverse

        # Attempt Nominatim reverse lookup
        try:
            nom_url = "https://nominatim.openstreetmap.org/reverse"
            nom_params: dict[str, str | float | int] = {
                "lat": snapped_lat,
                "lon": snapped_lon,
                "format": "json",
                "addressdetails": 1,
            }
            headers = {"User-Agent": "Urbero-Urban-Air-Assistant/1.0 (contact@urbero.internal)"}
            async with httpx.AsyncClient(timeout=httpx.Timeout(4.0, connect=2.0)) as client:
                resp = await self._nominatim.request(
                    lambda: client.get(nom_url, params=nom_params, headers=headers)
                )
                if resp.status_code == 200:
                    data = resp.json()
                    addr = data.get("address", {})
                    suburb = addr.get("suburb", addr.get("neighbourhood", ""))
                    city = addr.get("city", addr.get("town", addr.get("county", "Unknown City")))
                    state = addr.get("state", "")
                    label_parts = [p for p in [suburb, city, state] if p]
                    label = ", ".join(label_parts) if label_parts else "Current Location"
                    res = ReverseGeocodeResult(
                        label=label,
                        city=city,
                        state=state,
                    )
                    expires_at = now + self.cache_ttl
                    self._store_reverse(grid_key, expires_at, res)
                    await self._shared.set_fresh(
                        shared_key, expires_at, res.model_dump(mode="json")
                    )
                    return res
        except Exception as err:
            logger.warning(
                "reverse_geocode_failed grid=%s error_type=%s", grid_key, type(err).__name__
            )

        # Fallback if reverse geocode times out
        fallback_res = ReverseGeocodeResult(
            label="Current Location",
            city="Local Area",
            state="India",
        )

        return fallback_res
