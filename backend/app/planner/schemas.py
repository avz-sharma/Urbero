"""SINGLE SOURCE OF TRUTH: Pydantic v2 schemas for FastAPI, Grok (xAI), and TypeScript generation.

Defines bounded request and response structures, transparency math breakdowns,
metadata contracts, and copy-ready briefing templates.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.app.aqi.confidence import ConfidenceResult
from backend.app.aqi.cpcb import CPCBAQIResult
from backend.app.aqi.diurnal import DiurnalProfileResult
from backend.app.config.constants import (
    DISCLAIMER_CIGARETTE_HEURISTIC,
    DISCLAIMER_EXPOSURE_BASELINES,
)
from backend.app.exposure.cadr import RoomCADRResult, RoomDimensions, RoomIndoorFactors
from backend.app.exposure.commute import CommuteModeComparison
from backend.app.exposure.errands import ErrandStop, MergedErrandsResult
from backend.app.exposure.optimizer import RoutineOptimizationResult, ScheduledActivity
from backend.app.providers.base import SensorReading


class HealthResponse(BaseModel):
    status: Literal["healthy"] = "healthy"
    service: Literal["urbero-backend"] = "urbero-backend"
    timestamp: str
    environment: str


class NearestStationResponse(BaseModel):
    station_name: str
    distance_km: float
    source: str
    status: Literal["live", "modelled_live", "stale"]
    is_reference_grade: bool | None
    observed_at: str
    readings: list[SensorReading]
    cpcb_aqi: CPCBAQIResult
    data_confidence: ConfidenceResult


class StationMetadataSchema(BaseModel):
    """Auditable sensor station metadata attached to every recommendation card."""

    source: str
    station: str
    distance_km: float
    observed_at: datetime
    fetched_at: datetime
    status: Literal["live", "modelled_live", "stale"]
    is_reference_grade: bool | None = None
    conversion_note: str = ""


class MathBreakdownSchema(BaseModel):
    """Show the Math transparency drawer details."""

    formula_name: str
    formula_expression: str
    inputs: dict[str, str | bool | int | float | None]
    output_value: float | str
    reference_benchmark: str
    scientific_citation: str


class RecommendationCard(BaseModel):
    """Transparent actionable recommendation card required by AGENTS.md."""

    id: str
    pillar: Literal["routine", "indoor", "impact"]
    title: str
    why: str = Field(min_length=10)
    quantified_impact: str = Field(min_length=10)
    math_breakdown: MathBreakdownSchema
    station_metadata: StationMetadataSchema
    data_confidence: Literal["High", "Medium", "Low"]
    confidence_reason: str


class WhatsAppFamilyCard(BaseModel):
    """Copy-ready daily WhatsApp card for Indian families."""

    model_config = ConfigDict(extra="forbid")

    headline: str
    language: Literal["english", "hinglish"]
    current_aqi_badge: str
    key_actions: list[str] = Field(min_length=2)
    commute_tip: str
    indoor_tip: str
    sensitive_member_alert: str
    formatted_message: str


class CommunityBrief(BaseModel):
    """Copy-ready community briefing for RWAs and schools."""

    model_config = ConfigDict(extra="forbid")

    rwa_society_advisory: str
    school_outdoor_activity_recommendation: str
    mask_and_health_guidance: str
    formatted_brief: str


class NarrativeBriefings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    whatsapp_card: WhatsAppFamilyCard
    community_brief: CommunityBrief


class DailyPlanRequest(BaseModel):
    """Incoming request for daily plan generation."""

    city: str = Field(default="Delhi", min_length=2, max_length=160)
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    household_preset_id: str | None = None
    room_dimensions: RoomDimensions = Field(
        default_factory=lambda: RoomDimensions(length_m=5.0, width_m=4.0, height_m=2.8)
    )
    indoor_factors: RoomIndoorFactors = Field(default_factory=RoomIndoorFactors)
    activities: list[ScheduledActivity] = Field(default_factory=list, max_length=32)
    commute_distance_km: float = Field(default=12.0, gt=0)
    errands: list[ErrandStop] = Field(default_factory=list, max_length=4)
    language_preference: Literal["english", "hinglish"] = "english"
    untrusted_notes: str | None = Field(default=None, max_length=300)


class ExposureReferenceLabels(BaseModel):
    cigarette_heuristic: str = DISCLAIMER_CIGARETTE_HEURISTIC
    reference_values: str = DISCLAIMER_EXPOSURE_BASELINES


class DailyPlanResponse(BaseModel):
    """Complete personalized response with deterministic math and narrative edge."""

    timestamp: datetime
    city: str
    station_metadata: StationMetadataSchema
    aqi_result: CPCBAQIResult
    data_confidence: ConfidenceResult
    smog_episode_active: bool
    medical_disclaimer: str = ""
    routine_optimization: RoutineOptimizationResult
    commute_comparisons: list[CommuteModeComparison]
    room_cadr_guidance: RoomCADRResult
    errand_merger: MergedErrandsResult | None = None
    whatsapp_card: WhatsAppFamilyCard
    community_brief: CommunityBrief
    recommendation_cards: list[RecommendationCard] = Field(default_factory=list)
    diurnal_profile: DiurnalProfileResult | None = None
    history_source: str = "Unavailable; schedule timing optimization disabled."
    exposure_reference_labels: ExposureReferenceLabels = Field(
        default_factory=ExposureReferenceLabels
    )


class TravelAdviceRequest(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    distance_km: float = Field(gt=0, le=200)
    question: str = Field(min_length=1, max_length=300)


class TravelChoice(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: str
    priority: Literal["exposure", "emissions", "time", "balance"]


PlannerProvider = Literal["grok", "gemini", "groq"]


class TravelAdviceResponse(BaseModel):
    recommendation: CommuteModeComparison
    priority: Literal["exposure", "emissions", "time", "balance"]
    source: Literal[PlannerProvider, "fallback_template"]
    smog_advisory: str


class RoomVisionExtraction(BaseModel):
    """Structured extraction from a room photograph for CADR form pre-fill."""

    is_valid_room: bool
    rejection_reason: str | None = None
    estimated_length_m: float = Field(default=5.0, ge=1.0, le=20.0)
    estimated_width_m: float = Field(default=4.0, ge=1.0, le=20.0)
    estimated_height_m: float = Field(default=2.8, ge=1.5, le=6.0)
    has_kitchen_chimney: bool = False
    burns_incense_agarbatti: bool = False
    has_unsealed_balcony: bool = False
    confidence_score: float = Field(default=0.8, ge=0.0, le=1.0)
    explanation: str


class ModelledPollutantHour(BaseModel):
    """Hourly modelled air quality prediction from atmospheric simulation."""

    time: str
    pm25_ug_m3: float
    pm10_ug_m3: float
    no2_ug_m3: float | None = None
    co_ug_m3: float | None = None


class ModelledForecastResponse(BaseModel):
    """Labelled modelled air quality forecast structurally separated from live sensor data."""

    source: str = "Open-Meteo / Copernicus Atmosphere Monitoring Service (CAMS)"
    is_modelled_forecast: bool = True
    latitude: float
    longitude: float
    timezone: str
    hourly_forecasts: list[ModelledPollutantHour]
    mandatory_disclaimer: str = (
        "NOTICE: Modelled atmospheric forecasts are mathematical simulations from CAMS / ECMWF. "
        "They are NOT ground-truth physical sensor measurements and must be interpreted separately "
        "from WAQI/CPCB live station data."
    )


class LocationSearchResult(BaseModel):
    """India-scoped geocoded location search item."""

    label: str
    city: str
    state: str
    lat: float = Field(ge=-90.0, le=90.0)
    lon: float = Field(ge=-180.0, le=180.0)


class ReverseGeocodeResult(BaseModel):
    """Reverse geocoding result with administrative labels."""

    label: str
    city: str
    state: str
