"""Unit tests for brute-force multi-stop errand merger."""

import pytest

from backend.app.exposure.errands import (
    ErrandStop,
    optimize_errands,
)


def test_two_stop_loop_returns_applied_emissions_factor_and_fractional_times() -> None:
    stops = [
        ErrandStop(
            id="pharmacy",
            name="Pharmacy",
            category="pharmacy",
            duration_minutes=5,
            distance_from_home_km=1,
        ),
        ErrandStop(
            id="groceries",
            name="Groceries",
            category="groceries",
            duration_minutes=10,
            distance_from_home_km=2,
        ),
    ]

    result = optimize_errands(stops, 13.25, 16, 80, 40)

    assert [stop.id for stop in result.ordered_stops] == ["pharmacy", "groceries"]
    assert result.travel_mode == "petrol_2w"
    assert result.model_dump()["emissions_factor_g_per_km"] == 48
    assert result.baseline_separate_distance_km == 6
    assert result.merged_loop_distance_km == 4.4
    assert result.distance_saved_km == 1.6
    assert result.tailpipe_co2_saved_grams == 76.8
    assert result.recommended_start_hour == 13.25
    assert result.recommended_end_hour == 13.676
    assert "13:15" in result.rationale
    assert "13:41" in result.rationale


def test_waiting_can_increase_dose_in_the_cleaner_window() -> None:
    pickup = ErrandStop(
        id="pickup",
        name="School pickup",
        category="school_pickup",
        duration_minutes=10,
        distance_from_home_km=1,
        window_open_hour=15,
        window_close_hour=15.5,
    )

    result = optimize_errands([pickup], 13, 16, 80, 40)

    assert result.baseline_inhaled_pm25_ug == 13.8
    assert result.optimized_inhaled_pm25_ug == 61.8
    assert result.pm25_dose_reduction_percent == -347.8
    assert "increases" in result.rationale
    assert "347.8%" in result.rationale


def test_four_stop_loop_keeps_the_first_equally_ranked_ordering() -> None:
    stops = [
        ErrandStop(
            id=str(distance),
            name=f"Stop {distance}",
            category="groceries",
            duration_minutes=5,
            distance_from_home_km=distance,
        )
        for distance in range(1, 5)
    ]

    result = optimize_errands(stops, 13, 16, 80, 40)

    assert [stop.id for stop in result.ordered_stops] == ["1", "2", "3", "4"]
    assert result.merged_loop_distance_km == 10.4
    assert result.recommended_end_hour == 13.7493


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
