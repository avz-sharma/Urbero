"""Location search and reverse geocoding endpoints."""

import logging

from fastapi import APIRouter, HTTPException, Query, Request, status

from backend.app.api.security import limiter
from backend.app.planner.schemas import LocationSearchResult, ReverseGeocodeResult
from backend.app.providers.geocoding import GeocodingProvider

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/locations", tags=["locations"])
geocoding_provider = GeocodingProvider()


@router.get("/search", response_model=list[LocationSearchResult])
@limiter.limit("60/minute")
async def search_locations_endpoint(
    request: Request,
    q: str = Query(
        ...,
        min_length=2,
        max_length=100,
        description="Search string for Indian city, locality, or sector",
    ),
) -> list[LocationSearchResult]:
    """Search Indian cities and localities with 24-hour caching."""
    clean_q = q.strip()
    if len(clean_q) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Query string must be at least 2 characters.",
        )
    return await geocoding_provider.search_locations(clean_q)


@router.get("/reverse", response_model=ReverseGeocodeResult)
@limiter.limit("60/minute")
async def reverse_geocode_endpoint(
    request: Request,
    lat: float = Query(..., ge=-90.0, le=90.0, description="Latitude [-90, 90]"),
    lon: float = Query(..., ge=-180.0, le=180.0, description="Longitude [-180, 180]"),
) -> ReverseGeocodeResult:
    """Reverse geocode GPS coordinates with 2-decimal privacy snapping and 24-hour caching."""
    return await geocoding_provider.reverse_geocode(lat, lon)
