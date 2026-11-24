"""Pure brute-force errand merger for up to 4 stops.

Optimizes multi-stop local trips (groceries, pharmacy, bank, school pickup) to minimize
travel distance, avoid tailpipe CO2, and schedule outdoor exposure into the cleanest diurnal window.
Respects fixed time windows (e.g. school pickup, bank hours).
Zero I/O.
"""

import itertools
from typing import Final

from pydantic import BaseModel, Field

from backend.app.config.constants import COMMUTE_CO2_GRAMS_PER_KM

MAX_ERRAND_STOPS: Final[int] = 4


class ErrandStop(BaseModel):
    """Destination stop for an errand with spatial and temporal constraints."""

    id: str
    name: str
    category: str  # groceries, pharmacy, bank, school_pickup
    duration_minutes: float = Field(gt=0)
    distance_from_home_km: float = Field(gt=0)
    window_open_hour: float | None = None  # e.g. 10.0 for 10:00 AM
    window_close_hour: float | None = None  # e.g. 16.0 for 4:00 PM


class MergedErrandsResult(BaseModel):
    """Optimized consolidated errand loop with quantified environmental and lung benefits."""

    ordered_stops: list[ErrandStop]
    recommended_start_hour: float
    recommended_end_hour: float
    baseline_separate_distance_km: float
    merged_loop_distance_km: float
    distance_saved_km: float
    travel_mode: str
    tailpipe_co2_saved_grams: float
    baseline_inhaled_pm25_ug: float
    optimized_inhaled_pm25_ug: float
    pm25_dose_reduction_percent: float
    rationale: str


def _estimate_interstop_distance(d1: float, d2: float) -> float:
    """Clustered distance approximation between two stops originating from home."""
    return round(abs(d1 - d2) + 0.4 * min(d1, d2), 2)


def optimize_errands(
    stops: list[ErrandStop],
    cleanest_window_start_hour: float = 13.0,
    cleanest_window_end_hour: float = 16.0,
    peak_smog_avg_pm25: float | None = None,
    cleanest_window_avg_pm25: float | None = None,
    travel_mode: str = "petrol_2w",
) -> MergedErrandsResult:
    """Evaluate all permutations (<= 24) to find optimal multi-stop consolidation."""
    if not stops:
        raise ValueError("At least one errand stop is required.")
    if len(stops) > MAX_ERRAND_STOPS:
        raise ValueError(
            f"Errand optimizer supports up to {MAX_ERRAND_STOPS} stops (found {len(stops)})."
        )

    if peak_smog_avg_pm25 is None or cleanest_window_avg_pm25 is None:
        raise ValueError("Explicit pollutant concentrations are required; no synthetic baselines.")
    if not 0 <= cleanest_window_start_hour < cleanest_window_end_hour <= 24:
        raise ValueError("Invalid scheduling window")
    if peak_smog_avg_pm25 < 0 or cleanest_window_avg_pm25 < 0:
        raise ValueError("Concentrations must be non-negative")
    if travel_mode not in COMMUTE_CO2_GRAMS_PER_KM:
        raise ValueError("Unknown travel mode")

    baseline_distance = round(sum(2.0 * s.distance_from_home_km for s in stops), 2)
    best: tuple[float, float, float, tuple[ErrandStop, ...], float] | None = None
    # Evaluate each ordering with travel, waiting, service and return-home time.
    # Scheduling starts at the requested cleanest window; waiting is included in dose.
    for perm in itertools.permutations(stops):
        clock = cleanest_window_start_hour
        distance = 0.0
        previous = 0.0
        feasible = True
        for stop in perm:
            leg = (
                stop.distance_from_home_km
                if previous == 0
                else _estimate_interstop_distance(previous, stop.distance_from_home_km)
            )
            distance += leg
            clock += leg / 25.0
            if stop.window_open_hour is not None:
                clock = max(clock, stop.window_open_hour)
            clock += stop.duration_minutes / 60
            if stop.window_close_hour is not None and clock > stop.window_close_hour + 1e-9:
                feasible = False
                break
            previous = stop.distance_from_home_km
        if not feasible:
            continue
        distance += perm[-1].distance_from_home_km
        clock += perm[-1].distance_from_home_km / 25
        if clock > cleanest_window_end_hour + 1e-9:
            continue
        candidate = (round(distance, 2), clock, cleanest_window_start_hour, perm, clock)
        if best is None or candidate[:3] < best[:3]:
            best = candidate
    if best is None:
        raise ValueError("No feasible errand loop satisfies all stop and scheduling windows.")
    best_loop_dist, _, start_time, best_order, end_time = best
    best_perm = list(best_order)
    end_time = round(end_time, 4)
    distance_saved = round(max(0.0, baseline_distance - best_loop_dist), 2)
    total_activity_mins = sum(s.duration_minutes for s in best_perm)
    total_loop_duration_hours = end_time - start_time

    # 4. Quantified carbon avoided
    co2_factor = COMMUTE_CO2_GRAMS_PER_KM.get(travel_mode, 48.0)
    co2_saved = round(distance_saved * co2_factor, 1)

    # 5. Inhaled dose reduction
    # Baseline separate trips taken at peak hours:
    baseline_travel_hours = baseline_distance / 25.0
    baseline_exposure_hours = baseline_travel_hours + (total_activity_mins / 60.0)
    baseline_dose = round(peak_smog_avg_pm25 * 0.70 * baseline_exposure_hours, 1)

    # Consolidated loop scheduled in cleanest afternoon window:
    optimized_dose = round(cleanest_window_avg_pm25 * 0.70 * total_loop_duration_hours, 1)
    dose_reduction_pct = (
        round(((baseline_dose - optimized_dose) / baseline_dose) * 100.0, 1)
        if baseline_dose > 0
        else 0.0
    )

    rationale = (
        f"Consolidating {len(stops)} separate round-trips into a single loop reduces travel from "
        f"{baseline_distance} km to {best_loop_dist} km ({distance_saved} km saved, avoiding {co2_saved}g CO2). "
        f"Timing the loop between {int(start_time):02d}:{int((start_time % 1) * 60):02d} and "
        f"{int(end_time):02d}:{int((end_time % 1) * 60):02d} lowers personal PM2.5 exposure by {dose_reduction_pct}%."
    )

    return MergedErrandsResult(
        ordered_stops=best_perm,
        recommended_start_hour=start_time,
        recommended_end_hour=end_time,
        baseline_separate_distance_km=baseline_distance,
        merged_loop_distance_km=best_loop_dist,
        distance_saved_km=distance_saved,
        travel_mode=travel_mode,
        tailpipe_co2_saved_grams=co2_saved,
        baseline_inhaled_pm25_ug=baseline_dose,
        optimized_inhaled_pm25_ug=optimized_dose,
        pm25_dose_reduction_percent=dose_reduction_pct,
        rationale=rationale,
    )
