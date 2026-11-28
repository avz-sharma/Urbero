"""India-scoped Geocoding Provider with 24-hour caching and privacy-first coordinate snapping.

Provides fast locality/city searching and reverse geocoding using Open-Meteo Geocoding
and Nominatim APIs with fallbacks to verified Indian metropolitan landmarks.
"""

import asyncio
import logging
import time
from collections.abc import Callable
from typing import Any

import httpx
from pydantic import TypeAdapter, ValidationError

from backend.app.planner.schemas import LocationSearchResult, ReverseGeocodeResult
from backend.app.providers.cache import SupabaseCache
from backend.app.providers.resilience import ResilientGet, UpstreamUnavailable, coalesce

logger = logging.getLogger(__name__)
SEARCH_RESULTS = TypeAdapter(list[LocationSearchResult])
SEARCH_LIMIT = 5
NOMINATIM_HEADERS = {"User-Agent": "Urbero-Urban-Air-Assistant/1.0 (contact@urbero.internal)"}


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


def _parse_open_meteo_row(item: dict[str, Any]) -> LocationSearchResult | None:
    if str(item.get("country_code", "")).upper() != "IN":
        return None
    city = item["name"]
    state = item.get("admin1", city)
    return LocationSearchResult(
        label=f"{city}, {state}, India",
        city=city,
        state=state,
        lat=item["latitude"],
        lon=item["longitude"],
    )


def _parse_nominatim_row(item: dict[str, Any], query: str) -> LocationSearchResult | None:
    address = item.get("address", {})
    if str(address.get("country_code", "in")).lower() != "in":
        return None
    city = address.get("city", address.get("town", address.get("suburb", query)))
    state = address.get("state", "India")
    locality = item["display_name"].split(",", maxsplit=1)[0]
    return LocationSearchResult(
        label=f"{locality}, {city}, {state}",
        city=city,
        state=state,
        lat=item["lat"],
        lon=item["lon"],
    )


def _add_provider_results(
    results: list[LocationSearchResult],
    rows: object,
    parse: Callable[[dict[str, Any]], LocationSearchResult | None],
    provider: str,
) -> None:
    if not isinstance(rows, list):
        return
    for row in rows:
        try:
            if not isinstance(row, dict):
                raise TypeError("Expected an object")
            candidate = parse(row)
        except (AttributeError, KeyError, TypeError, ValidationError):
            logger.warning("geocoding_row_invalid provider=%s", provider)
            continue
        if candidate is None or any(
            abs(known.lat - candidate.lat) < 0.01 and abs(known.lon - candidate.lon) < 0.01
            for known in results
        ):
            continue
        results.append(
            candidate.model_copy(
                update={"lat": round(candidate.lat, 4), "lon": round(candidate.lon, 4)}
            )
        )
        if len(results) == SEARCH_LIMIT:
            break


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
        shared_key = self._shared.search_key(norm_key)
        cached = await self._cached_search(norm_key, shared_key, now)
        if cached is not None:
            return cached

        results = [
            loc
            for loc in CURATED_INDIAN_LOCATIONS
            if any(norm_key in field.lower() for field in (loc.label, loc.city, loc.state))
        ][:SEARCH_LIMIT]
        if len(results) < SEARCH_LIMIT:
            await self._search_open_meteo(clean_query, results)

        # Keep Nominatim results, which can include more precise addresses, in L1 only.
        can_share = bool(results)
        if not results:
            await self._search_nominatim(clean_query, results)
        if results:
            expires_at = now + self.cache_ttl
            self._store_search(norm_key, expires_at, results)
            if shared_key is not None and can_share:
                await self._shared.set_fresh(
                    shared_key,
                    expires_at,
                    {"results": SEARCH_RESULTS.dump_python(results, mode="json")},
                )
        return results

    async def _cached_search(
        self, key: str, shared_key: str | None, now: float
    ) -> list[LocationSearchResult] | None:
        cached = self._search_cache.get(key)
        if cached is not None and now < cached[0]:
            return cached[1]
        if shared_key is None or not (shared := await self._shared.get_fresh(shared_key)):
            return None
        expires_at, data = shared
        try:
            results = SEARCH_RESULTS.validate_python(data.get("results"))[:SEARCH_LIMIT]
        except ValidationError:
            logger.warning("cache_payload_invalid tier=l2 provider=location_search")
            return None
        self._store_search(key, expires_at, results)
        return results

    async def _search_open_meteo(self, query: str, results: list[LocationSearchResult]) -> None:
        url = "https://geocoding-api.open-meteo.com/v1/search"
        params = {"name": query, "count": "10", "language": "en", "format": "json"}
        data = await _fetch_search(self._openmeteo, url, params)
        if isinstance(data, dict):
            _add_provider_results(results, data.get("results"), _parse_open_meteo_row, "open_meteo")

    async def _search_nominatim(self, query: str, results: list[LocationSearchResult]) -> None:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": query,
            "countrycodes": "in",
            "format": "json",
            "limit": str(SEARCH_LIMIT),
            "addressdetails": "1",
        }
        data = await _fetch_search(self._nominatim, url, params, headers=NOMINATIM_HEADERS)
        _add_provider_results(
            results, data, lambda row: _parse_nominatim_row(row, query), "nominatim"
        )

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
            async with httpx.AsyncClient(timeout=httpx.Timeout(4.0, connect=2.0)) as client:
                resp = await self._nominatim.request(
                    lambda: client.get(nom_url, params=nom_params, headers=NOMINATIM_HEADERS)
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


async def _fetch_search(
    resilient: ResilientGet,
    url: str,
    params: dict[str, str],
    *,
    headers: dict[str, str] | None = None,
) -> object:
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(5.0, connect=3.0)) as client:
            response = await resilient.request(
                lambda: client.get(url, params=params, headers=headers)
            )
            response.raise_for_status()
            if response.status_code != 200:
                return None
            return response.json()
    except (httpx.HTTPError, UpstreamUnavailable, ValueError) as error:
        logger.warning(
            "geocoding_search_failed host=%s error_type=%s",
            httpx.URL(url).host,
            type(error).__name__,
        )
        return None
