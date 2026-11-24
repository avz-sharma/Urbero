"""FastAPI application routes and endpoint contracts."""

import logging
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, FastAPI, File, HTTPException, Query, Request, UploadFile, status
from fastapi.staticfiles import StaticFiles
from slowapi.middleware import SlowAPIMiddleware

from backend.app.api.locations import router as locations_router
from backend.app.api.security import limiter, sanitize_user_input, setup_security
from backend.app.aqi.confidence import ConfidenceInput, calculate_data_confidence
from backend.app.aqi.cpcb import CPCBAQIResult, calculate_cpcb_aqi, calculate_sub_index
from backend.app.aqi.diurnal import compute_diurnal_profile
from backend.app.config.constants import DISCLAIMER_SMOG_EPISODE
from backend.app.exposure.cadr import (
    RoomCADRResult,
    RoomDimensions,
    RoomIndoorFactors,
    calculate_room_cadr,
)
from backend.app.exposure.commute import CommuteModeComparison, compare_commute_modes
from backend.app.exposure.dose import (
    DoseCalculationInput,
    DoseCalculationResult,
    calculate_inhaled_dose,
)
from backend.app.exposure.errands import ErrandStop, MergedErrandsResult, optimize_errands
from backend.app.exposure.optimizer import optimize_daily_routine
from backend.app.exposure.transit import has_metro
from backend.app.planner.grok import GrokPlannerClient
from backend.app.planner.schemas import (
    DailyPlanRequest,
    DailyPlanResponse,
    ModelledForecastResponse,
    RoomVisionExtraction,
    StationMetadataSchema,
    TravelAdviceRequest,
    TravelAdviceResponse,
)
from backend.app.planner.vision import analyze_room_photo
from backend.app.providers.base import SensorReading
from backend.app.providers.openmeteo import OpenMeteoProvider
from backend.app.providers.pipeline import AirQualityPipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")
router.include_router(locations_router)
openmeteo_provider = OpenMeteoProvider()
air_quality = AirQualityPipeline(model=openmeteo_provider)
grok_client = GrokPlannerClient()


async def _get_pollutants(
    latitude: float, longitude: float
) -> tuple[SensorReading, dict[str, float]]:
    try:
        readings = await air_quality.get_latest_readings(latitude, longitude)
        return readings[0], {reading.parameter: reading.value for reading in readings}
    except Exception as err:
        logger.warning("plan_data_unavailable error_type=%s", type(err).__name__)
        raise HTTPException(
            status_code=503, detail="Air quality is temporarily unavailable. Please retry."
        ) from err


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint for Cloud Run container probes."""
    return {
        "status": "healthy",
        "service": "urbero-backend",
        "timestamp": datetime.now(UTC).isoformat(),
        "environment": os.getenv("ENVIRONMENT", "production"),
    }


@router.get("/stations/nearest")
@limiter.limit("60/minute")
async def get_nearest_station_readings(
    request: Request,
    lat: float = Query(..., ge=-90.0, le=90.0, description="Latitude"),
    lon: float = Query(..., ge=-180.0, le=180.0, description="Longitude"),
) -> dict[str, Any]:
    """Fetch nearest station readings, calculate CPCB AQI, and score data confidence."""
    try:
        readings = await air_quality.get_latest_readings(lat, lon)
    except Exception as err:
        logger.warning("air_quality_unavailable error_type=%s", type(err).__name__)
        raise HTTPException(
            status_code=503, detail="Air quality is temporarily unavailable. Please retry."
        ) from err

    readings_dict = {r.parameter: r.value for r in readings}
    first = readings[0]

    aqi_res = calculate_cpcb_aqi(readings_dict)
    conf_res = calculate_data_confidence(
        ConfidenceInput(
            distance_km=first.distance_km,
            observed_at=first.observed_at,
            fetched_at=first.fetched_at,
            pollutants_present=list(readings_dict.keys()),
            is_reference_grade=first.is_reference_grade,
            is_modelled="Modelled" in first.source,
        )
    )

    return {
        "station_name": first.station,
        "distance_km": first.distance_km,
        "source": first.source,
        "status": first.status,
        "is_reference_grade": first.is_reference_grade,
        "observed_at": first.observed_at.isoformat(),
        "readings": [r.model_dump() for r in readings],
        "cpcb_aqi": aqi_res.model_dump(),
        "data_confidence": conf_res.model_dump(),
    }


@router.post("/aqi/calculate", response_model=CPCBAQIResult)
async def calculate_aqi_endpoint(readings: dict[str, float]) -> CPCBAQIResult:
    """Calculate CPCB AQI from a dictionary of pollutant concentrations."""
    return calculate_cpcb_aqi(readings)


@router.post("/exposure/dose", response_model=DoseCalculationResult)
async def calculate_dose_endpoint(inp: DoseCalculationInput) -> DoseCalculationResult:
    """Calculate personal inhaled PM2.5 dose and cigarette equivalence."""
    return calculate_inhaled_dose(inp)


@router.post("/exposure/cadr", response_model=RoomCADRResult)
async def calculate_cadr_endpoint(
    dimensions: RoomDimensions,
    factors: RoomIndoorFactors | None = None,
    target_ach: float = Query(5.0, gt=0, le=20),
) -> RoomCADRResult:
    """Calculate room purifier CADR requirement and indoor sealing actions."""
    return calculate_room_cadr(dimensions, factors, target_ach)


@router.post("/exposure/commute", response_model=list[CommuteModeComparison])
async def compare_commute_endpoint(
    distance_km: float = Query(..., gt=0),
    ambient_pm25: float = Query(..., ge=0),
) -> list[CommuteModeComparison]:
    """Compare commute modes on personal inhaled PM2.5 and tailpipe CO2."""
    return compare_commute_modes(distance_km, ambient_pm25)


@router.post("/exposure/commute/advice", response_model=TravelAdviceResponse)
@limiter.limit("20/minute")
async def advise_commute(request: Request, travel: TravelAdviceRequest) -> TravelAdviceResponse:
    question = sanitize_user_input(travel.question)
    if not question:
        raise HTTPException(status_code=422, detail="Enter a travel question.")
    station, pollutants = await _get_pollutants(travel.latitude, travel.longitude)
    pm25 = pollutants["PM2.5"]
    aqi = calculate_cpcb_aqi(pollutants)
    index = (
        aqi.overall_aqi
        if aqi.is_valid
        else (aqi.indicative_aqi or calculate_sub_index("PM2.5", pm25))
    )
    smog = index > 300
    options = compare_commute_modes(
        travel.distance_km, pm25, include_metro=has_metro(travel.latitude, travel.longitude)
    )
    eligible = [
        option for option in options if not smog or option.mode not in {"walking", "cycling"}
    ]
    choice = await grok_client.choose_travel_mode(
        question, eligible, pm25, station.status, smog, aqi_category=aqi.category
    )
    by_mode = {option.mode: option for option in eligible}
    return TravelAdviceResponse(
        recommendation=by_mode[choice.mode]
        if choice
        else min(eligible, key=lambda option: option.personal_inhaled_pm25_ug),
        priority=choice.priority if choice else "exposure",
        source=("gemini" if grok_client.gemini.api_key else "grok")
        if choice
        else "fallback_template",
        smog_advisory=DISCLAIMER_SMOG_EPISODE if smog else "",
    )


@router.post("/exposure/errands", response_model=MergedErrandsResult)
async def optimize_errands_endpoint(
    stops: list[ErrandStop],
    peak_pm25: float = Query(..., ge=0, le=2000),
    window_pm25: float = Query(..., ge=0, le=2000),
) -> MergedErrandsResult:
    """Optimize multi-stop local trips into a consolidated loop."""
    try:
        return optimize_errands(
            stops, peak_smog_avg_pm25=peak_pm25, cleanest_window_avg_pm25=window_pm25
        )
    except ValueError as err:
        raise HTTPException(status_code=422, detail=str(err)) from err


@router.post(
    "/plan/daily",
    response_model=DailyPlanResponse,
)
@router.post("/plan", response_model=DailyPlanResponse)
@limiter.limit("20/minute")
async def generate_daily_plan(request: Request, plan_req: DailyPlanRequest) -> DailyPlanResponse:
    """End-to-end personalized daily plan: deterministic calculations with GenAI edge narrative."""
    # 1. Fetch live or cached station readings
    first, readings_dict = await _get_pollutants(plan_req.latitude, plan_req.longitude)

    # 2. Deterministic Core Computations
    aqi_res = calculate_cpcb_aqi(readings_dict)
    conf_res = calculate_data_confidence(
        ConfidenceInput(
            distance_km=first.distance_km,
            observed_at=first.observed_at,
            fetched_at=first.fetched_at,
            pollutants_present=list(readings_dict.keys()),
            is_reference_grade=first.is_reference_grade,
            is_modelled="Modelled" in first.source,
        )
    )

    # Archived CAMS hours are modelled, never fabricated or labelled station history.
    diurnal = None
    history_source = "Unavailable; schedule timing optimization disabled."
    pm25 = readings_dict["PM2.5"]
    hourly_pm25 = {}
    try:
        history = await openmeteo_provider.get_history(plan_req.latitude, plan_req.longitude)
        diurnal = compute_diurnal_profile("Open-Meteo CAMS model grid", history)
        hourly_pm25 = {h.hour: h.avg_pm25 for h in diurnal.hourly_curve if h.sample_count}
        history_source = "Open-Meteo CAMS (Modelled) — last 72h archived model output, not empirical station history."
    except Exception as err:
        logger.warning("history_unavailable error_type=%s", type(err).__name__)

    # Optimize activities
    routine_res = optimize_daily_routine(
        plan_req.activities,
        hourly_pm25,
        current_aqi=aqi_res.overall_aqi
        if aqi_res.is_valid
        else (aqi_res.indicative_aqi or calculate_sub_index("PM2.5", pm25)),
        current_pm25=pm25,
    )

    # Commute comparison
    commute_res = compare_commute_modes(
        plan_req.commute_distance_km,
        ambient_pm25_ug_m3=pm25,
        include_metro=has_metro(plan_req.latitude, plan_req.longitude),
    )

    # Room CADR guidance
    cadr_res = calculate_room_cadr(plan_req.room_dimensions, plan_req.indoor_factors)

    # Errands optimization
    try:
        errands_res = (
            optimize_errands(
                plan_req.errands,
                cleanest_window_start_hour=float(diurnal.cleanest_window_start)
                if diurnal and diurnal.cleanest_window_end > diurnal.cleanest_window_start
                else 6,
                cleanest_window_end_hour=float(diurnal.cleanest_window_end)
                if diurnal and diurnal.cleanest_window_end > diurnal.cleanest_window_start
                else 22,
                peak_smog_avg_pm25=diurnal.peak_smog_avg_pm25 if diurnal else pm25,
                cleanest_window_avg_pm25=diurnal.cleanest_window_avg_pm25 if diurnal else pm25,
            )
            if plan_req.errands
            else None
        )
    except ValueError as err:
        raise HTTPException(
            status_code=422,
            detail="No feasible errand loop in the available window. Adjust stop times.",
        ) from err

    # Station metadata
    st_meta = StationMetadataSchema(
        source=first.source,
        station=first.station,
        distance_km=first.distance_km,
        observed_at=first.observed_at,
        fetched_at=first.fetched_at,
        status=first.status,
        is_reference_grade=first.is_reference_grade,
        conversion_note=first.conversion_note,
    )

    # 3. GenAI Edge: Briefings & Cards
    clean_notes = sanitize_user_input(plan_req.untrusted_notes or "")
    wa_card, comm_brief, cards = await grok_client.generate_plan_briefings(
        city=plan_req.city,
        station=st_meta,
        aqi=aqi_res,
        confidence=conf_res,
        routine=routine_res,
        commute_options=commute_res,
        cadr=cadr_res,
        errands=errands_res,
        language=plan_req.language_preference,
        untrusted_notes=clean_notes,
    )
    location_label = " ".join(sanitize_user_input(plan_req.city).split())
    wa_card.formatted_message = f"Location: {location_label}\n\n{wa_card.formatted_message}"

    for card in cards:
        card.math_breakdown.inputs["pollutant_conversion"] = first.conversion_note
        card.math_breakdown.inputs["history_source"] = history_source

    return DailyPlanResponse(
        medical_disclaimer=routine_res.smog_episode_advisory,
        timestamp=datetime.now(UTC),
        city=plan_req.city,
        station_metadata=st_meta,
        aqi_result=aqi_res,
        data_confidence=conf_res,
        smog_episode_active=routine_res.smog_episode_active,
        routine_optimization=routine_res,
        commute_comparisons=commute_res,
        room_cadr_guidance=cadr_res,
        errand_merger=errands_res,
        whatsapp_card=wa_card,
        community_brief=comm_brief,
        recommendation_cards=cards,
        diurnal_profile=diurnal,
        history_source=history_source,
    )


@router.post("/planner/vision", response_model=RoomVisionExtraction)
@limiter.limit("15/minute")
async def analyze_room_photo_endpoint(
    request: Request,
    file: UploadFile = File(..., description="Room photograph to prefill CADR parameters"),
) -> RoomVisionExtraction:
    """Analyze a room photograph to pre-fill CADR form fields with confidence scores."""
    content_type = file.content_type or ""
    try:
        image_bytes = await file.read()
        return analyze_room_photo(
            image_bytes=image_bytes,
            content_type=content_type,
            grok_client=grok_client,
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err)
        ) from val_err
    except Exception as err:
        logger.error("vision_failed error_type=%s", type(err).__name__)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze room photo.",
        ) from err


@router.get("/forecast/modelled", response_model=ModelledForecastResponse)
@limiter.limit("30/minute")
async def get_modelled_forecast(
    request: Request,
    lat: float = Query(..., ge=-90.0, le=90.0, description="Latitude"),
    lon: float = Query(..., ge=-180.0, le=180.0, description="Longitude"),
) -> ModelledForecastResponse:
    """Fetch hourly modelled air quality forecast (Open-Meteo CAMS simulation)."""
    try:
        return await openmeteo_provider.fetch_forecast(lat, lon)
    except Exception as err:
        logger.warning("forecast_unavailable error_type=%s", type(err).__name__)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Modelled forecast temporarily unavailable.",
        ) from err


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Urbero Air Quality Assistant API",
        version="0.1.0",
        description="Production GenAI assistant for Indian cities with deterministic calculation core.",
    )
    setup_security(app)
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    app.include_router(router)
    frontend_dist = Path(__file__).resolve().parents[3] / "frontend" / "dist"
    if frontend_dist.is_dir():
        app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
    return app


app = create_app()
