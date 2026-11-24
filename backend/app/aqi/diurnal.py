"""Station-history (24-72h) diurnal profiler.

Analyzes empirical multi-day station telemetry to extract 24-hour diurnal air quality curves,
identifying daily inversion peaks and optimal low-smog outdoor activity windows.
Zero fabricated curves; strictly derived from recorded station measurements.
"""

from collections import defaultdict
from datetime import datetime

from pydantic import BaseModel, Field


class HourlyMeasurement(BaseModel):
    """Historical timestamped pollutant concentration measurement."""

    observed_at: datetime
    value: float = Field(ge=0.0, allow_inf_nan=False)


class DiurnalHourProfile(BaseModel):
    """Statistical summary for a single hour of the day (0-23)."""

    hour: int = Field(ge=0, le=23)
    avg_pm25: float
    sample_count: int


class DiurnalProfileResult(BaseModel):
    """Derived 24-hour empirical diurnal profile and activity timing windows."""

    station_name: str
    hourly_curve: list[DiurnalHourProfile]
    cleanest_window_start: int
    cleanest_window_end: int
    cleanest_window_avg_pm25: float
    peak_smog_hours: list[int]
    peak_smog_avg_pm25: float
    total_samples: int
    summary_advisory: str


def compute_diurnal_profile(
    station_name: str,
    measurements: list[HourlyMeasurement],
    min_required_samples: int = 24,
) -> DiurnalProfileResult:
    """Compute empirical 24-hour diurnal profile from historical station measurements."""
    if len(measurements) < min_required_samples:
        raise ValueError(
            f"Insufficient historical data to derive diurnal profile: {len(measurements)} samples "
            f"(minimum {min_required_samples} required)."
        )

    # Group by hour of day (0..23 in local station time)
    hour_buckets: dict[int, list[float]] = defaultdict(list)
    for m in measurements:
        if m.value >= 0.0:
            hour_buckets[m.observed_at.hour].append(m.value)

    hourly_curve: list[DiurnalHourProfile] = []
    hourly_means: dict[int, float] = {}

    for h in range(24):
        vals = hour_buckets.get(h, [])
        if not vals:
            continue
        mean_val = round(sum(vals) / len(vals), 1)
        hourly_means[h] = mean_val
        hourly_curve.append(
            DiurnalHourProfile(
                hour=h,
                avg_pm25=mean_val,
                sample_count=len(vals),
            )
        )

    # Find 3-hour contiguous cleanest window
    best_start = 13
    best_avg = float("inf")

    # Only evaluate windows where data exists
    for start_h in range(24):
        h1 = start_h
        h2 = (start_h + 1) % 24
        h3 = (start_h + 2) % 24

        counts = [len(hour_buckets.get(h, [])) for h in [h1, h2, h3]]
        if all(c > 0 for c in counts):
            avg_window = (hourly_means[h1] + hourly_means[h2] + hourly_means[h3]) / 3.0
            if avg_window < best_avg:
                best_avg = avg_window
                best_start = start_h

    cleanest_end = (best_start + 3) % 24
    if best_avg == float("inf"):
        raise ValueError("Insufficient historical data: no complete three-hour window")

    # Identify peak smog hours (hours exceeding 75th percentile of hourly averages)
    active_means = [m for h, m in hourly_means.items() if len(hour_buckets.get(h, [])) > 0]
    sorted_means = sorted(active_means)
    p75_threshold = sorted_means[int(len(sorted_means) * 0.75)] if sorted_means else 0.0

    peak_hours = [
        h
        for h, m in hourly_means.items()
        if m >= p75_threshold and len(hour_buckets.get(h, [])) > 0
    ]
    peak_avg = (
        round(sum(hourly_means[h] for h in peak_hours) / len(peak_hours), 1) if peak_hours else 0.0
    )

    advisory = (
        f"Cleanest ambient air window is observed between {best_start:02d}:00 and {cleanest_end:02d}:00 "
        f"(averaging ~{best_avg:.1f} µg/m³). Avoid strenuous outdoor exertion during peak smog "
        f"hours ({', '.join(f'{h:02d}:00' for h in peak_hours[:4])})."
    )

    return DiurnalProfileResult(
        station_name=station_name,
        hourly_curve=hourly_curve,
        cleanest_window_start=best_start,
        cleanest_window_end=cleanest_end,
        cleanest_window_avg_pm25=round(best_avg, 1),
        peak_smog_hours=sorted(peak_hours),
        peak_smog_avg_pm25=peak_avg,
        total_samples=len(measurements),
        summary_advisory=advisory,
    )
