"""API failure, schema, streamed-size and non-leaking error regressions."""

import logging
from unittest.mock import AsyncMock

import pytest
from starlette.testclient import TestClient

from backend.app.api import routes
from backend.app.api.locations import geocoding_provider
from backend.app.api.security import MAX_PAYLOAD_BYTES, limiter
from backend.app.planner.schemas import DailyPlanResponse
from backend.app.providers.openmeteo import OpenMeteoProvider
from backend.app.providers.pipeline import AirQualityPipeline
from backend.app.providers.waqi import WAQIProvider
from backend.tests.fixtures.providers import model_client


def test_real_provider_failure_returns_generic_503(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        routes.air_quality,
        "get_latest_readings",
        AsyncMock(side_effect=RuntimeError("secret-token lat=28.12345678")),
    )
    client = TestClient(routes.app)
    for response in [
        client.get("/api/stations/nearest?lat=28.61&lon=77.21"),
        client.post("/api/plan/daily", json={"latitude": 28.61, "longitude": 77.21}),
    ]:
        assert response.status_code == 503
        assert "secret-token" not in response.text
        assert "temporarily unavailable" in response.text


def test_replayed_pipeline_schema_and_conversion_math(monkeypatch: pytest.MonkeyPatch) -> None:
    model = OpenMeteoProvider(model_client())
    monkeypatch.setattr(routes, "air_quality", AirQualityPipeline(WAQIProvider(token=""), model))
    monkeypatch.setattr(routes, "openmeteo_provider", model)
    client = TestClient(routes.app)
    nearest = client.get("/api/stations/nearest?lat=28.61&lon=77.21")
    assert nearest.status_code == 200
    assert nearest.json()["status"] == "modelled_live"
    response = client.post("/api/plan/daily", json={"latitude": 28.61, "longitude": 77.21})
    assert response.status_code == 200
    plan = DailyPlanResponse.model_validate(response.json())
    assert plan.station_metadata.source == "Open-Meteo CAMS (Modelled)"
    assert plan.data_confidence.level == "Low"
    assert "not empirical station history" in plan.history_source
    assert all(
        "CO" in card.math_breakdown.inputs["pollutant_conversion"]
        for card in plan.recommendation_cards
    )


def test_missing_history_preserves_real_reading_without_curve(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = OpenMeteoProvider(model_client())
    monkeypatch.setattr(routes, "air_quality", AirQualityPipeline(WAQIProvider(token=""), model))
    monkeypatch.setattr(
        routes.openmeteo_provider, "get_history", AsyncMock(side_effect=ValueError("missing"))
    )
    response = TestClient(routes.app).post(
        "/api/plan/daily", json={"latitude": 28.61, "longitude": 77.21}
    )
    assert response.status_code == 200
    assert response.json()["diurnal_profile"] is None
    assert "disabled" in response.json()["history_source"]


def test_kashmir_plan_and_restricted_travel_options(monkeypatch: pytest.MonkeyPatch) -> None:
    model = OpenMeteoProvider(model_client())
    monkeypatch.setattr(routes, "air_quality", AirQualityPipeline(WAQIProvider(token=""), model))
    monkeypatch.setattr(routes, "openmeteo_provider", model)
    chooser = AsyncMock(return_value=None)
    monkeypatch.setattr(routes.grok_client, "choose_travel_mode", chooser)
    client = TestClient(routes.app)
    coordinates = {"latitude": 34.0837, "longitude": 74.7973}
    response = client.post("/api/plan/daily", json={**coordinates, "city": "Srinagar, Kashmir"})
    assert response.status_code == 200
    plan = DailyPlanResponse.model_validate(response.json())
    assert not plan.routine_optimization.activities
    assert plan.whatsapp_card.formatted_message.startswith("Location: Srinagar, Kashmir\n")
    assert {mode.mode for mode in plan.commute_comparisons} == {
        "bus_public",
        "auto_rickshaw",
        "walking",
        "cycling",
        "petrol_2w",
        "petrol_car_solo",
    }
    assert all("Petrol" not in mode.label for mode in plan.commute_comparisons)
    assert "Metro" not in plan.whatsapp_card.commute_tip
    advice = client.post(
        "/api/exposure/commute/advice",
        json={
            **coordinates,
            "distance_km": 8,
            "question": "How should I travel?",
        },
    )
    assert advice.status_code == 200
    assert advice.json()["source"] == "fallback_template"
    assert all(option.mode != "metro" for option in chooser.await_args.args[1])


def test_chunked_body_limit_and_error_headers() -> None:
    response = TestClient(routes.app).post(
        "/api/plan/daily", content=iter([b" " * (MAX_PAYLOAD_BYTES // 2)] * 3)
    )
    assert response.status_code == 413
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_api_csp_and_room_size_validation() -> None:
    client = TestClient(routes.app)
    response = client.get("/api/health")
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]
    assert (
        "'unsafe-inline'" not in response.headers["Content-Security-Policy"].split("style-src")[0]
    )
    response = client.post(
        "/api/exposure/cadr",
        json={
            "dimensions": {"length_m": 1e100, "width_m": 4, "height_m": 3},
        },
    )
    assert response.status_code == 422


@pytest.mark.parametrize(
    ("field", "invalid"),
    [
        ("pm25_concentration_ug_m3", -1),
        ("duration_minutes", -1),
        ("breathing_rate_m3_per_hr", 0),
    ],
)
def test_invalid_dose_inputs_return_422(field: str, invalid: float) -> None:
    payload = {
        "pm25_concentration_ug_m3": 50.0,
        "duration_minutes": 30.0,
        "breathing_rate_m3_per_hr": 1.0,
    }
    payload[field] = invalid
    response = TestClient(routes.app, raise_server_exceptions=False).post(
        "/api/exposure/dose", json=payload
    )
    assert response.status_code == 422


def test_location_rate_limit_omits_client_ip_from_logs(
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(geocoding_provider, "search_locations", AsyncMock(return_value=[]))
    address = "203.0.113.62"
    with TestClient(routes.app, client=(address, 1234)) as client, caplog.at_level(logging.WARNING):
        for _ in range(61):
            response = client.get("/api/locations/search", params={"q": "Delhi"})
    limiter.reset()
    assert response.status_code == 429
    assert address not in caplog.text


def test_errand_validation_and_forecast_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    client = TestClient(routes.app)
    assert (
        client.post("/api/exposure/errands?peak_pm25=100&window_pm25=50", json=[]).status_code
        == 422
    )
    monkeypatch.setattr(
        routes.openmeteo_provider, "fetch_forecast", AsyncMock(side_effect=ValueError("secret"))
    )
    response = client.get("/api/forecast/modelled?lat=28.61&lon=77.21")
    assert response.status_code == 502
    assert "secret" not in response.text
