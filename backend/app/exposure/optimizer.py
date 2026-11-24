"""Pure daily household routine re-optimizer and Smog Episode trigger.

Re-schedules flexible household activities around diurnal inversion smog peaks,
quantifies before/after personal inhaled dose reductions, and activates Smog Episode Mode
at Very Poor / Severe AQI with strict honesty guardrails (fitted N95/FFP2, no cloth masks, consult doctor).
Zero I/O.
"""

from math import ceil, floor, isfinite
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from backend.app.config.constants import (
    BREATHING_RATES_M3_PER_HR,
    DISCLAIMER_SMOG_EPISODE,
    INDOOR_INFILTRATION_FACTORS,
)


class ScheduledActivity(BaseModel):
    """An individual household member's daily scheduled event."""

    id: str
    name: str = Field(min_length=1, max_length=80)
    member_name: str = Field(min_length=1, max_length=80)
    age_group: Literal["adult", "child", "senior"] = "adult"
    intensity: Literal["resting", "sedentary", "light", "moderate", "heavy"] = "moderate"
    scheduled_start_hour: float = Field(ge=0.0, le=24.0)
    scheduled_end_hour: float = Field(ge=0.0, le=24.0)
    is_outdoor: bool = True
    is_flexible: bool = True
    indoor_purifier_active: bool = False

    @model_validator(mode="after")
    def validate_time_range(self) -> "ScheduledActivity":
        if self.scheduled_end_hour <= self.scheduled_start_hour:
            raise ValueError("End time must be after start time on the same day.")
        return self


class OptimizedActivity(BaseModel):
    """Adjusted activity schedule with before/after inhaled PM2.5 exposure."""

    activity_id: str
    activity_name: str
    member_name: str
    original_start_hour: float
    original_end_hour: float
    optimized_start_hour: float
    optimized_end_hour: float
    is_shifted: bool
    is_shifted_indoors: bool
    baseline_inhaled_pm25_ug: float
    optimized_inhaled_pm25_ug: float
    dose_reduction_ug: float
    recommendation_note: str


class RoutineOptimizationResult(BaseModel):
    """Complete household schedule re-optimization summary and episode advisory."""

    activities: list[OptimizedActivity]
    total_baseline_dose_ug: float
    total_optimized_dose_ug: float
    total_dose_reduction_ug: float
    total_dose_reduction_percent: float
    smog_episode_active: bool
    smog_episode_advisory: str
    clean_air_day: bool
    overall_advisory: str


def _window_mean(hourly_pm25: dict[int, float], start: float, end: float) -> float | None:
    total = 0.0
    for hour in range(floor(start), ceil(end)):
        concentration = hourly_pm25.get(hour)
        if concentration is None:
            return None
        overlap = min(end, hour + 1) - max(start, hour)
        total += concentration * overlap
    return total / (end - start)


def optimize_daily_routine(
    activities: list[ScheduledActivity],
    hourly_pm25: dict[int, float],
    current_aqi: int,
    current_pm25: float | None = None,
) -> RoutineOptimizationResult:
    """Optimize household activities across diurnal slots and evaluate Smog Episode trigger."""
    if any(not isfinite(v) or v < 0 for v in hourly_pm25.values()):
        raise ValueError("Hourly concentrations must be finite and non-negative")
    if current_pm25 is None and not hourly_pm25:
        raise ValueError("A measured/modelled concentration is required")

    # 1. Smog Episode Mode trigger (Very Poor / Severe AQI > 300)
    smog_episode_active = current_aqi > 300
    clean_air_day = current_aqi <= 100

    optimized_items: list[OptimizedActivity] = []
    total_baseline_dose = 0.0
    total_optimized_dose = 0.0

    for act in activities:
        duration_hours = act.scheduled_end_hour - act.scheduled_start_hour
        b_rate = BREATHING_RATES_M3_PER_HR[act.age_group][act.intensity]

        # Calculate baseline concentration at scheduled hour
        baseline_ambient_pm25 = _window_mean(
            hourly_pm25, act.scheduled_start_hour, act.scheduled_end_hour
        )
        if baseline_ambient_pm25 is None:
            if current_pm25 is None:
                raise ValueError("Missing activity-hour data and no current concentration")
            baseline_ambient_pm25 = current_pm25

        baseline_factor = 1.0 if act.is_outdoor else INDOOR_INFILTRATION_FACTORS["closed_windows"]
        if not act.is_outdoor and act.indoor_purifier_active:
            baseline_factor *= 0.15

        baseline_dose = round(baseline_ambient_pm25 * baseline_factor * b_rate * duration_hours, 1)

        # Optimization logic
        new_start = act.scheduled_start_hour
        new_end = act.scheduled_end_hour
        is_shifted = False
        shifted_indoors = False
        note = "Scheduled as planned."

        if clean_air_day:
            note = "Good air quality day: Outdoor activity encouraged."
            opt_dose = baseline_dose
        elif smog_episode_active and act.is_outdoor:
            if act.is_flexible:
                # Shift indoors with active purifier
                shifted_indoors = True
                new_factor = INDOOR_INFILTRATION_FACTORS["closed_windows"] * 0.15  # HEPA
                opt_dose = round(baseline_ambient_pm25 * new_factor * b_rate * duration_hours, 1)
                note = (
                    "Smog Episode Alert: Rescheduled to indoor exercise with HEPA purifier active."
                )
            else:
                # Fixed outdoor activity (e.g. school commute)
                note = (
                    "Mandatory outdoor trip during Severe AQI: Wear a fitted N95/FFP2 respirator mask. "
                    "Cloth masks do not filter PM2.5."
                )
                # N95 mask cuts inhaled dose by ~80%
                opt_dose = round(baseline_ambient_pm25 * 0.20 * b_rate * duration_hours, 1)
        elif act.is_outdoor and act.is_flexible:
            # Enumerate complete daylight slots from supplied history, no invented curve.
            candidates = [
                (value, hour)
                for hour in range(6, 22)
                if hour + duration_hours <= 22
                and (value := _window_mean(hourly_pm25, hour, hour + duration_hours)) is not None
            ]
            best = min(candidates) if candidates else None
            if best and best[0] < baseline_ambient_pm25:
                clean_ambient_pm25, cleanest_window_start = best
                is_shifted = True
                new_start = float(cleanest_window_start)
                new_end = new_start + duration_hours
                opt_dose = round(clean_ambient_pm25 * b_rate * duration_hours, 1)
                note = (
                    f"Moved to the lowest available history-derived daylight slot, starting "
                    f"at {cleanest_window_start:02d}:00."
                )
            else:
                opt_dose = baseline_dose
        else:
            opt_dose = baseline_dose

        dose_diff = round(max(0.0, baseline_dose - opt_dose), 1)
        total_baseline_dose += baseline_dose
        total_optimized_dose += opt_dose

        optimized_items.append(
            OptimizedActivity(
                activity_id=act.id,
                activity_name=act.name,
                member_name=act.member_name,
                original_start_hour=act.scheduled_start_hour,
                original_end_hour=act.scheduled_end_hour,
                optimized_start_hour=new_start,
                optimized_end_hour=new_end,
                is_shifted=is_shifted,
                is_shifted_indoors=shifted_indoors,
                baseline_inhaled_pm25_ug=baseline_dose,
                optimized_inhaled_pm25_ug=opt_dose,
                dose_reduction_ug=dose_diff,
                recommendation_note=note,
            )
        )

    total_reduction_ug = round(max(0.0, total_baseline_dose - total_optimized_dose), 1)
    total_pct = (
        round((total_reduction_ug / total_baseline_dose) * 100.0, 1)
        if total_baseline_dose > 0
        else 0.0
    )

    episode_advisory = DISCLAIMER_SMOG_EPISODE if smog_episode_active else ""

    if not activities:
        overall = "Add a household activity to estimate exposure and compare times."
    elif smog_episode_active:
        overall = (
            f"⚠️ Smog Episode Active (AQI {current_aqi}). All sensitive members (children, asthmatics, seniors) "
            f"should remain indoors. Flexible outdoor activities have been shifted indoors with HEPA purification, "
            f"cutting household inhaled PM2.5 by {total_pct}%."
        )
    elif clean_air_day:
        overall = "Clean air window today! Ambient AQI is Satisfactory. Enjoy outdoor activities; natural ventilation is encouraged."
    else:
        overall = (
            f"Optimizing flexible activity slots using available hourly history reduces total household "
            f"inhaled PM2.5 dose by {total_reduction_ug} µg ({total_pct}% reduction)."
        )

    return RoutineOptimizationResult(
        activities=optimized_items,
        total_baseline_dose_ug=round(total_baseline_dose, 1),
        total_optimized_dose_ug=round(total_optimized_dose, 1),
        total_dose_reduction_ug=total_reduction_ug,
        total_dose_reduction_percent=total_pct,
        smog_episode_active=smog_episode_active,
        smog_episode_advisory=episode_advisory,
        clean_air_day=clean_air_day,
        overall_advisory=overall,
    )
