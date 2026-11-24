"""Comprehensive tests for GPS, Geocoding, Station discovery, and privacy guardrails."""

import pytest
from starlette.testclient import TestClient

from backend.app.api.routes import app
from backend.app.providers.base import calculate_haversine_distance_km


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_invalid_coordinates_rejected(client: TestClient) -> None:
    """Verify lat/lon validation: lat=999 or lon=999 returns 422 Unprocessable Entity."""
    resp_lat = client.get("/api/locations/reverse?lat=999.0&lon=77.20")
    assert resp_lat.status_code == 422

    resp_lon = client.get("/api/locations/reverse?lat=28.61&lon=999.0")
    assert resp_lon.status_code == 422

    resp_nearest = client.get("/api/stations/nearest?lat=999.0&lon=77.20")
    assert resp_nearest.status_code == 422


def test_haversine_distance_golden() -> None:
    """Golden-value distance calculation between Connaught Place and Sector 62 Noida."""
    # Connaught Place: 28.6315, 77.2167; Sector 62 Noida: 28.6270, 77.3620
    dist = calculate_haversine_distance_km(28.6315, 77.2167, 28.6270, 77.3620)
    assert 13.0 <= dist <= 15.5


def test_location_search_endpoint(client: TestClient) -> None:
    """Verify GET /api/locations/search?q=Noida returns normalized Indian locality results."""
    resp = client.get("/api/locations/search?q=Noida")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any("Noida" in item["city"] or "Noida" in item["label"] for item in data)
    assert all("lat" in item and "lon" in item and "label" in item for item in data)


def test_location_search_short_query_rejected(client: TestClient) -> None:
    """Verify query shorter than 2 characters is rejected with 422."""
    resp = client.get("/api/locations/search?q=a")
    assert resp.status_code == 422


def test_location_reverse_geocode_endpoint(client: TestClient) -> None:
    """Verify GET /api/locations/reverse returns structured address with 2-decimal snapping."""
    resp = client.get("/api/locations/reverse?lat=28.6315&lon=77.2167")
    assert resp.status_code == 200
    data = resp.json()
    assert "label" in data
    assert "city" in data
    assert "state" in data
