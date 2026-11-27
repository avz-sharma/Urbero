"""Orchestrate provider history, pure calculations and daily-plan briefings."""

import logging
from datetime import UTC, datetime

from backend.app.api.security import sanitize_user_input
from backend.app.aqi.confidence import ConfidenceInput, ConfidenceResult, calculate_data_confidence
from backend.app.aqi.cpcb import CPCBAQIResult, calculate_cpcb_aqi, calculate_sub_index
from backend.app.aqi.diurnal import DiurnalProfileResult, compute_diurnal_profile
from backend.app.exposure.cadr import calculate_room_cadr
from backend.app.exposure.commute import compare_commute_modes
from backend.app.exposure.errands import ErrandStop, MergedErrandsResult, optimize_errands
from backend.app.exposure.optimizer import optimize_daily_routine
from backend.app.exposure.transit import has_metro
from backend.app.planner.grok import GrokPlannerClient
from backend.app.planner.schemas import DailyPlanRequest, DailyPlanResponse, StationMetadataSchema
from backend.app.providers.base import SensorReading
from backend.app.providers.openmeteo import OpenMeteoProvider

logger = logging.getLogger(__name__)


def reading_evidence(
    first: SensorReading, pollutants: dict[str, float]
) -> tuple[CPCBAQIResult, ConfidenceResult]:
    return calculate_cpcb_aqi(pollutants), calculate_data_confidence(
        ConfidenceInput(
            distance_km=first.distance_km,
            observed_at=first.observed_at,
            fetched_at=first.fetched_at,
            pollutants_present=list(pollutants),
            is_reference_grade=first.is_reference_grade,
            is_modelled="Modelled" in first.source,
        )
    )


def advisory_index(aqi: CPCBAQIResult, pm25: float) -> int:
    if aqi.is_valid:
        return aqi.overall_aqi
    if aqi.indicative_aqi is not None:
        return aqi.indicative_aqi
    return calculate_sub_index("PM2.5", pm25)


class InfeasibleErrandLoop(ValueError):
    """Submitted stop constraints could not produce a feasible route."""


def build_errand_loop(
    stops: list[ErrandStop], diurnal: DiurnalProfileResult | None, pm25: float
) -> MergedErrandsResult | None:
    if not stops:
        return None
    start, end = 6.0, 22.0
    if diurnal and diurnal.cleanest_window_end > diurnal.cleanest_window_start:
        start, end = float(diurnal.cleanest_window_start), float(diurnal.cleanest_window_end)
    try:
        return optimize_errands(
            stops,
            cleanest_window_start_hour=start,
            cleanest_window_end_hour=end,
            peak_smog_avg_pm25=diurnal.peak_smog_avg_pm25 if diurnal else pm25,
            cleanest_window_avg_pm25=diurnal.cleanest_window_avg_pm25 if diurnal else pm25,
        )
    except ValueError as err:
        raise InfeasibleErrandLoop(
            "No feasible errand loop in the available window. Adjust stop times."
        ) from err


async def assemble_daily_plan(
    plan: DailyPlanRequest,
    first: SensorReading,
    readings_dict: dict[str, float],
    history_provider: OpenMeteoProvider,
    planner: GrokPlannerClient,
) -> DailyPlanResponse:
    aqi_res, conf_res = reading_evidence(first, readings_dict)
    # Archived CAMS hours are modelled, never fabricated or labelled station history.
    diurnal = None
    history_source = "Unavailable; schedule timing optimization disabled."
    pm25 = readings_dict["PM2.5"]
    hourly_pm25 = {}
    try:
        history = await history_provider.get_history(plan.latitude, plan.longitude)
        diurnal = compute_diurnal_profile("Open-Meteo CAMS model grid", history)
        hourly_pm25 = {h.hour: h.avg_pm25 for h in diurnal.hourly_curve if h.sample_count}
        history_source = "Open-Meteo CAMS (Modelled) — last 72h archived model output, not empirical station history."
    except Exception as err:
        logger.warning("history_unavailable error_type=%s", type(err).__name__)

    # Optimize activities
    routine_res = optimize_daily_routine(
        plan.activities,
        hourly_pm25,
        current_aqi=advisory_index(aqi_res, pm25),
        current_pm25=pm25,
    )

    # Commute comparison
    commute_res = compare_commute_modes(
        plan.commute_distance_km,
        ambient_pm25_ug_m3=pm25,
        include_metro=has_metro(plan.latitude, plan.longitude),
    )

    # Room CADR guidance
    cadr_res = calculate_room_cadr(plan.room_dimensions, plan.indoor_factors)

    errands_res = build_errand_loop(plan.errands, diurnal, pm25)

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
    clean_notes = sanitize_user_input(plan.untrusted_notes or "")
    wa_card, comm_brief, cards = await planner.generate_plan_briefings(
        city=plan.city,
        station=st_meta,
        aqi=aqi_res,
        confidence=conf_res,
        routine=routine_res,
        commute_options=commute_res,
        cadr=cadr_res,
        errands=errands_res,
        language=plan.language_preference,
        untrusted_notes=clean_notes,
    )
    location_label = " ".join(sanitize_user_input(plan.city).split())
    wa_card.formatted_message = f"Location: {location_label}\n\n{wa_card.formatted_message}"

    for card in cards:
        card.math_breakdown.inputs["pollutant_conversion"] = first.conversion_note
        card.math_breakdown.inputs["history_source"] = history_source

    return DailyPlanResponse(
        medical_disclaimer=routine_res.smog_episode_advisory,
        timestamp=datetime.now(UTC),
        city=plan.city,
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
