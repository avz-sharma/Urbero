"""Deterministic template fallback generator for briefings and recommendation cards.

Guarantees 100% system availability with zero math hallucination even during upstream
LLM quota exhaustion, network partitions, or response validation failures.
"""

from typing import Literal

from backend.app.aqi.confidence import ConfidenceResult
from backend.app.aqi.cpcb import CPCBAQIResult
from backend.app.config.constants import (
    DISCLAIMER_CIGARETTE_HEURISTIC,
    DISCLAIMER_EXPOSURE_BASELINES,
    DISCLAIMER_SMOG_EPISODE,
)
from backend.app.exposure.cadr import RoomCADRResult
from backend.app.exposure.commute import CommuteModeComparison
from backend.app.exposure.errands import MergedErrandsResult
from backend.app.exposure.optimizer import RoutineOptimizationResult
from backend.app.planner.schemas import (
    CommunityBrief,
    MathBreakdownSchema,
    RecommendationCard,
    StationMetadataSchema,
    WhatsAppFamilyCard,
)


def generate_deterministic_fallback(
    city: str,
    station: StationMetadataSchema,
    aqi: CPCBAQIResult,
    confidence: ConfidenceResult,
    routine: RoutineOptimizationResult,
    commute_options: list[CommuteModeComparison],
    cadr: RoomCADRResult,
    errands: MergedErrandsResult | None,
    language: Literal["english", "hinglish"] = "english",
) -> tuple[WhatsAppFamilyCard, CommunityBrief, list[RecommendationCard]]:
    """Synthesize structured briefings and cards using certified deterministic templates."""
    is_smog = routine.smog_episode_active
    aqi_cat = aqi.category
    aqi_val = str(aqi.overall_aqi) if aqi.is_valid else "unavailable (insufficient pollutants)"

    lower_exposure = min(commute_options, key=lambda option: option.personal_inhaled_pm25_ug)
    public_transit = next((option for option in commute_options if option.mode == "metro"), None)
    transit_label = public_transit.label if public_transit else "Public Bus"

    # 1. WhatsApp Family Card
    if language == "hinglish":
        headline = f"🌅 Urbero Air Alert ({city}) — AQI {aqi_val} ({aqi_cat})"
        badge = f"AQI {aqi_val} | {aqi_cat} ({station.station})"
        commute_tip = (
            f"Commute Tip: Road pe bike/walk se bachiye. Agar available ho, {lower_exposure.label} consider karein."
            if is_smog
            else f"Commute Tip: Agar route par available ho, {transit_label} consider karein."
        )
        indoor_tip = f"Indoor Tip: Kamre mein HEPA purifier ~{cadr.required_cadr_m3_per_hr} m³/h run karein. Balcony gaps seal karein."
        sensitive_tip = (
            "Elderly aur bachon ko outdoor morning walk/play strictly avoid karna chahiye. Bahar nikalna zaroori ho toh fitted N95 mask pehnein."
            if is_smog
            else "Outdoor planning ke liye current pollution aur available history dekhein."
        )
        actions = [
            f"Total dose reduction: Family exposure {routine.total_dose_reduction_percent}% kam ki gayi hai schedule shift se.",
            "Cloth mask PM2.5 block nahi karta; agar outdoor trip mandatory hai toh N95 mask zaroor pehnein.",
        ]
    else:
        headline = f"🌅 Urbero Daily Family Air Briefing ({city})"
        badge = f"AQI {aqi_val} | {aqi_cat} ({station.station})"
        commute_tip = (
            f"Commute: Avoid active roadside travel in severe smog. Consider {lower_exposure.label} if available for your trip."
            if is_smog
            else f"Commute: Consider {transit_label} where it serves your route."
        )
        indoor_tip = f"Indoor Air: Run purifier at ~{cadr.required_cadr_m3_per_hr} m³/h CADR ({cadr.required_cadr_cfm} CFM). Keep balcony doors sealed."
        sensitive_tip = (
            "Sensitive Advisory: Asthmatics, seniors, and children must avoid morning outdoor exertion. Fitted N95/FFP2 required outdoors."
            if is_smog
            else "Use current pollution and available history to choose ventilation and activity times."
        )
        actions = [
            f"Household planning reduces estimated inhaled PM2.5 by {routine.total_dose_reduction_percent}%.",
            f"Purifier target ACH: {cadr.target_ach} changes/hr for {cadr.room_volume_m3} m³ room volume.",
        ]

    if not routine.activities:
        actions[0] = "Add your household schedule to compare activity times."
    if is_smog:
        sensitive_tip += " " + DISCLAIMER_SMOG_EPISODE
    schedule_summary = (
        f"Household dose reduction estimate: {routine.total_dose_reduction_ug} µg ({routine.total_dose_reduction_percent}%)."
        if routine.activities
        else "Add a household schedule to compare activity times."
    )
    formatted_msg = (
        f"{headline}\n\n"
        f"📊 Air Status: {badge}\n"
        f"🛡️ Data Confidence: {confidence.level} ({confidence.reason})\n\n"
        f"• {sensitive_tip}\n"
        f"• {commute_tip}\n"
        f"• {indoor_tip}\n\n"
        f"💡 Impact: {schedule_summary}\n"
        f"⚠️ Note: {DISCLAIMER_CIGARETTE_HEURISTIC}"
    )

    whatsapp_card = WhatsAppFamilyCard(
        headline=headline,
        language=language,
        current_aqi_badge=badge,
        key_actions=actions,
        commute_tip=commute_tip,
        indoor_tip=indoor_tip,
        sensitive_member_alert=sensitive_tip,
        formatted_message=formatted_msg,
    )

    # 2. Community Brief (RWA & School)
    if is_smog:
        rwa_advisory = (
            f"RWA Air Advisory: Elevated particulate pollution detected (AQI {aqi_val}, {station.station}). "
            "Reschedule society morning jogging hours and stop outdoor leaf/waste burning immediately. "
            "Ensure society security guards are equipped with fitted N95 respirators."
        )
        school_rec = (
            "School Outdoor Activities: Mandatory cancellation of outdoor morning assemblies, PT drills, and sports. "
            "Prefer indoor physical activity during this episode. "
            "Students traveling by bus/walking should wear fitted N95/FFP2 masks (cloth masks are ineffective)."
        )
        mask_guidance = (
            "Health & Mask Guidance: Cloth masks are not substitutes for fitted particulate respirators. "
            "Only well-fitted N95/FFP2 respirators provide adequate protection. Consult a doctor for personalized asthma action plans."
        )
    else:
        rwa_advisory = (
            f"RWA Community Update: {aqi_cat} (AQI {aqi_val}). "
            "Use available hourly history and current pollution before outdoor events or ventilation."
        )
        school_rec = "School Outdoor Activities: Check current readings and local advisories; reduce exertion when pollution rises."
        mask_guidance = "Use current pollution and individual needs for travel precautions; consult a doctor for sensitive members."

    comm_formatted = (
        f"🏛️ RWA & School Air Quality Briefing — {city}\n"
        f"Station: {station.station} ({station.distance_km:.1f} km, Status: {station.status.upper()})\n\n"
        f"1. RWA Action: {rwa_advisory}\n\n"
        f"2. School Guidance: {school_rec}\n\n"
        f"3. Mask Protocol: {mask_guidance}\n\n"
        f"Reference Baselines: {DISCLAIMER_EXPOSURE_BASELINES}"
    )

    community_brief = CommunityBrief(
        rwa_society_advisory=rwa_advisory,
        school_outdoor_activity_recommendation=school_rec,
        mask_and_health_guidance=mask_guidance,
        formatted_brief=comm_formatted,
    )

    # 3. Transparent Recommendation Cards
    cards: list[RecommendationCard] = []

    # Card 1: Low-Emission Routine & Commute
    best_commute = public_transit or lower_exposure
    cards.append(
        RecommendationCard(
            id="rec-commute",
            pillar="routine",
            title="Planet vs. Lungs Commute Optimization",
            why=(
                f"During high ambient pollution, personal inhaled PM2.5 varies drastically by travel mode. "
                f"{best_commute.label} produces an estimated {best_commute.tailpipe_co2_grams} g CO2 on this trip."
            ),
            quantified_impact=(
                f"{best_commute.label}: {best_commute.personal_inhaled_pm25_ug} µg estimated inhaled PM2.5; "
                f"{best_commute.tailpipe_co2_grams}g configured transport CO2 estimate."
            ),
            math_breakdown=MathBreakdownSchema(
                formula_name="Personal Inhaled Dose & Transit Carbon",
                formula_expression="Dose = Cp × Multiplier × BreathingRate × Duration; CO2 = Distance × Factor",
                inputs={
                    "distance_km": best_commute.distance_km,
                    "ambient_pm25_ug_m3": next(
                        (s.concentration for s in aqi.sub_indices if s.pollutant == "PM2.5"),
                        "unavailable",
                    ),
                    "mode": best_commute.mode,
                },
                output_value=f"{best_commute.personal_inhaled_pm25_ug} µg PM2.5 / {best_commute.tailpipe_co2_grams}g CO2",
                reference_benchmark="WHO 2021 24-hr guideline: 15 µg/m³ ambient equivalent",
                scientific_citation="Goel et al. (2015), Atmospheric Environment; ARAI emission factors",
            ),
            station_metadata=station,
            data_confidence=confidence.level,
            confidence_reason=confidence.reason,
        )
    )

    # Card 2: Indoor Air Quality & CADR
    cards.append(
        RecommendationCard(
            id="rec-indoor",
            pillar="indoor",
            title="Room CADR & Envelope Sealing Engine",
            why=(
                "Sealing gaps, controlling indoor sources and purifier sizing can reduce particulate exposure. "
                f"A properly sized {cadr.required_cadr_m3_per_hr} m³/h purifier achieves {cadr.target_ach} air changes/hr."
            ),
            quantified_impact=(
                f"Sizing estimate: {cadr.required_cadr_m3_per_hr} m³/h CADR for a {cadr.room_volume_m3} m³ room; "
                "actual removal depends on leakage, sources, placement and filter performance."
            ),
            math_breakdown=MathBreakdownSchema(
                formula_name="Clean Air Delivery Rate (CADR)",
                formula_expression="CADR (m³/h) = Volume_room (m³) × ACH_target × SourceMultiplier",
                inputs={
                    "room_volume_m3": cadr.room_volume_m3,
                    "target_ach": cadr.target_ach,
                },
                output_value=f"{cadr.required_cadr_m3_per_hr} m³/h ({cadr.required_cadr_cfm} CFM)",
                reference_benchmark="AHAM AC-1 standard (5 ACH recommended for high pollution)",
                scientific_citation="Chen & Zhao (2011), Indoor Air; ANSI/AHAM AC-1-2020",
            ),
            station_metadata=station,
            data_confidence=confidence.level,
            confidence_reason=confidence.reason,
        )
    )

    # Card 3: Impact Justification & Errand Loop
    if errands:
        cards.append(
            RecommendationCard(
                id="rec-errands",
                pillar="impact",
                title="Consolidated Multi-Stop Errand Loop",
                why=(
                    f"Consolidating {len(errands.ordered_stops)} separate errands into a single Travelling Salesman loop "
                    f"uses the configured time window and approximate inter-stop distances."
                ),
                quantified_impact=(
                    f"Saves {errands.distance_saved_km} km of travel, avoids {errands.tailpipe_co2_saved_grams}g CO2, "
                    f"and cuts personal PM2.5 dose by {errands.pm25_dose_reduction_percent}%."
                ),
                math_breakdown=MathBreakdownSchema(
                    formula_name="Brute-Force Permutation Errand Merger",
                    formula_expression="Distance_saved = BaselineSeparate - MergedLoop; CO2_saved = Distance_saved × Factor",
                    inputs={
                        "stops_count": len(errands.ordered_stops),
                        "baseline_distance_km": errands.baseline_separate_distance_km,
                        "merged_distance_km": errands.merged_loop_distance_km,
                    },
                    output_value=f"{errands.distance_saved_km} km saved ({errands.tailpipe_co2_saved_grams}g CO2 avoided)",
                    reference_benchmark="CPCB India tailpipe factors for urban two-wheelers (48 g CO2/km)",
                    scientific_citation="CPCB / ARAI vehicular emission inventories (2018)",
                ),
                station_metadata=station,
                data_confidence=confidence.level,
                confidence_reason=confidence.reason,
            )
        )

    return whatsapp_card, community_brief, cards
