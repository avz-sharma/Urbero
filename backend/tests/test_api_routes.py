"""FastAPI E2E integration smoke tests and security middleware tests."""

import io
from unittest.mock import patch

import pytest
from PIL import Image
from starlette.testclient import TestClient

from backend.app.api.routes import app
from backend.app.planner.schemas import ModelledForecastResponse, ModelledPollutantHour


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health_check_endpoint(client: TestClient) -> None:
    """Verify GET /api/health returns 200 and required fields."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "urbero-backend"


def test_security_headers_present(client: TestClient) -> None:
    """Verify security headers middleware sets defensive headers."""
    response = client.get("/api/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "max-age" in response.headers["Strict-Transport-Security"]


def test_calculate_aqi_endpoint(client: TestClient) -> None:
    """Verify POST /api/aqi/calculate returns valid CPCB AQI."""
    payload = {
        "PM2.5": 45.0,
        "PM10": 80.0,
        "NO2": 45.0,
    }
    response = client.post("/api/aqi/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is True
    assert data["overall_aqi"] == 80
    assert data["dominant_pollutant"] == "PM10"


def test_calculate_dose_endpoint(client: TestClient) -> None:
    """Verify POST /api/exposure/dose calculates inhaled dose."""
    payload = {
        "pm25_concentration_ug_m3": 120.0,
        "duration_minutes": 60.0,
        "breathing_rate_m3_per_hr": 1.2,
        "infiltration_factor": 1.0,
        "purifier_efficiency": 0.0,
    }
    response = client.post("/api/exposure/dose", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["inhaled_dose_ug"] == 144.0
    assert data["cigarette_equivalent"] > 0


def test_calculate_cadr_endpoint(client: TestClient) -> None:
    """Verify POST /api/exposure/cadr computes CADR."""
    payload = {
        "dimensions": {
            "length_m": 5.0,
            "width_m": 4.0,
            "height_m": 3.0,
        },
        "target_ach": 5.0,
    }
    response = client.post("/api/exposure/cadr", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["room_volume_m3"] == 60.0
    assert data["required_cadr_m3_per_hr"] == 300.0


def test_compare_commute_endpoint(client: TestClient) -> None:
    """Verify POST /api/exposure/commute returns mode comparisons."""
    response = client.post("/api/exposure/commute?distance_km=15.0&ambient_pm25=150.0")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3


def test_optimize_errands_endpoint(client: TestClient) -> None:
    """Verify POST /api/exposure/errands returns consolidated loop."""
    payload = [
        {
            "id": "1",
            "name": "Groceries",
            "category": "groceries",
            "duration_minutes": 15,
            "distance_from_home_km": 3.0,
        },
        {
            "id": "2",
            "name": "Pharmacy",
            "category": "pharmacy",
            "duration_minutes": 10,
            "distance_from_home_km": 2.0,
        },
    ]
    response = client.post("/api/exposure/errands?peak_pm25=240&window_pm25=95", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["distance_saved_km"] > 0
    assert data["tailpipe_co2_saved_grams"] > 0


@pytest.mark.parametrize("path", ["/api/plan", "/api/plan/daily"])
def test_generate_daily_plan_smoke(client: TestClient, path: str) -> None:
    """E2E smoke test for POST /api/plan/daily."""
    payload = {
        "city": "Delhi",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "commute_distance_km": 10.0,
        "language_preference": "english",
        "room_dimensions": {
            "length_m": 4.5,
            "width_m": 3.5,
            "height_m": 2.8,
        },
        "activities": [
            {
                "id": "act-1",
                "name": "Morning Walk",
                "member_name": "Dada Ji",
                "age_group": "senior",
                "intensity": "moderate",
                "scheduled_start_hour": 7.0,
                "scheduled_end_hour": 8.0,
                "is_outdoor": True,
                "is_flexible": True,
            }
        ],
        "errands": [
            {
                "id": "err-1",
                "name": "Local Chemist",
                "category": "pharmacy",
                "duration_minutes": 15,
                "distance_from_home_km": 2.5,
            }
        ],
    }
    from backend.app.api.routes import AirQualityPipeline
    from backend.app.providers.openmeteo import OpenMeteoProvider
    from backend.app.providers.waqi import WAQIProvider
    from backend.tests.fixtures.providers import model_client

    model = OpenMeteoProvider(client=model_client())
    with (
        patch(
            "backend.app.api.routes.air_quality",
            AirQualityPipeline(waqi=WAQIProvider(token=""), model=model),
        ),
        patch("backend.app.api.routes.openmeteo_provider", model),
    ):
        response = client.post(path, json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["city"] == "Delhi"
    assert "aqi_result" in data
    assert "whatsapp_card" in data
    assert "community_brief" in data
    assert len(data["recommendation_cards"]) >= 3
    assert data["errand_merger"]["emissions_factor_g_per_km"] == 48
    assert data["room_cadr_guidance"]["dimensions"] == payload["room_dimensions"]
    assert "communication heuristic" in data["exposure_reference_labels"]["cigarette_heuristic"]
    assert "reference values" in data["exposure_reference_labels"]["reference_values"]


def test_planner_vision_endpoint(client: TestClient) -> None:
    """Verify POST /api/planner/vision with test image."""
    buf = io.BytesIO()
    img = Image.new("RGB", (100, 100), color="green")
    img.save(buf, format="JPEG")
    buf.seek(0)

    response = client.post(
        "/api/planner/vision",
        files={"file": ("test_room.jpg", buf, "image/jpeg")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid_room"] is False
    assert data["confidence_score"] == 0
    assert data["estimated_length_m"] >= 1.0


def test_planner_vision_endpoint_invalid_mime(client: TestClient) -> None:
    """Verify POST /api/planner/vision rejects text or gif files."""
    response = client.post(
        "/api/planner/vision",
        files={"file": ("doc.txt", b"plain text", "text/plain")},
    )
    assert response.status_code == 400


def test_forecast_modelled_endpoint(client: TestClient) -> None:
    """Verify GET /api/forecast/modelled returns separated modelled forecasts."""
    mock_resp = ModelledForecastResponse(
        latitude=28.6139,
        longitude=77.2090,
        timezone="Asia/Kolkata",
        hourly_forecasts=[
            ModelledPollutantHour(
                time="2026-11-21T12:00",
                pm25_ug_m3=125.0,
                pm10_ug_m3=210.0,
            )
        ],
    )

    with patch("backend.app.api.routes.openmeteo_provider.fetch_forecast", return_value=mock_resp):
        response = client.get("/api/forecast/modelled?lat=28.6139&lon=77.2090")
        assert response.status_code == 200
        data = response.json()
        assert data["is_modelled_forecast"] is True
        assert "NOT ground-truth physical sensor measurements" in data["mandatory_disclaimer"]
