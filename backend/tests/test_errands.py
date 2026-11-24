"""Unit tests for brute-force multi-stop errand merger."""

import pytest

from backend.app.exposure.errands import (
    ErrandStop,
    optimize_errands,
)


def test_errand_merger_savings() -> None:
    """Test 3-stop errand consolidation yields distance, CO2, and dose reductions."""
    stops = [
        ErrandStop(
            id="s1",
            name="Mother Dairy Groceries",
            category="groceries",
            duration_minutes=15,
            distance_from_home_km=2.5,
        ),
        ErrandStop(
            id="s2",
            name="Apollo Pharmacy",
            category="pharmacy",
            duration_minutes=10,
            distance_from_home_km=3.8,
        ),
        ErrandStop(
            id="s3",
            name="SBI Bank Branch",
            category="bank",
            duration_minutes=25,
            distance_from_home_km=4.2,
            window_open_hour=10.0,
            window_close_hour=16.0,
        ),
    ]

    res = optimize_errands(
        stops,
        cleanest_window_start_hour=13.0,
        cleanest_window_end_hour=16.0,
        peak_smog_avg_pm25=240,
        cleanest_window_avg_pm25=95,
    )

    # Baseline separate round trips = 2*(2.5 + 3.8 + 4.2) = 21.0 km
    assert res.baseline_separate_distance_km == 21.0
    # Merged loop should be substantially shorter
    assert res.merged_loop_distance_km < res.baseline_separate_distance_km
    assert res.distance_saved_km > 0.0
    assert res.tailpipe_co2_saved_grams > 0.0
    assert res.pm25_dose_reduction_percent > 0.0
    assert 10.0 <= res.recommended_start_hour <= 16.0


def test_errand_max_stops_limit() -> None:
    """Verify optimizer enforces <= 4 stops limit."""
    five_stops = [
        ErrandStop(
            id=f"s{i}",
            name=f"Stop {i}",
            category="groceries",
            duration_minutes=10,
            distance_from_home_km=2.0,
        )
        for i in range(5)
    ]
    with pytest.raises(ValueError, match="supports up to 4 stops"):
        optimize_errands(five_stops)

    with pytest.raises(ValueError, match="At least one"):
        optimize_errands([])
