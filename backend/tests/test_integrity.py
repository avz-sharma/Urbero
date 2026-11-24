"""Regression tests for integrity gaps exposed during the staff audit."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from backend.app.aqi.cpcb import calculate_cpcb_aqi
from backend.app.exposure.dose import DoseCalculationInput, calculate_inhaled_dose
from backend.app.exposure.errands import ErrandStop, optimize_errands


def test_fixed_school_window_requires_feasible_order() -> None:
    stops = [
        ErrandStop(
            id="shop",
            name="Groceries",
            category="groceries",
            duration_minutes=45,
            distance_from_home_km=1,
            window_open_hour=13,
            window_close_hour=18,
        ),
        ErrandStop(
            id="school",
            name="School",
            category="school_pickup",
            duration_minutes=5,
            distance_from_home_km=3,
            window_open_hour=13,
            window_close_hour=13.3,
        ),
    ]
    result = optimize_errands(
        stops,
        cleanest_window_start_hour=13,
        cleanest_window_end_hour=16,
        peak_smog_avg_pm25=150,
        cleanest_window_avg_pm25=80,
    )
    assert result.ordered_stops[0].id == "school"
    assert result.recommended_end_hour <= 16


def test_impossible_windows_rejected() -> None:
    stop = ErrandStop(
        id="s",
        name="Bank",
        category="bank",
        duration_minutes=60,
        distance_from_home_km=10,
        window_open_hour=13,
        window_close_hour=13.1,
    )
    with pytest.raises(ValueError, match="feasible"):
        optimize_errands([stop], peak_smog_avg_pm25=150, cleanest_window_avg_pm25=80)


@given(st.floats(min_value=0, max_value=1000), st.floats(min_value=0.1, max_value=2))
def test_activity_breathing_rate_monotonicity(concentration: float, rate: float) -> None:
    base = DoseCalculationInput(
        pm25_concentration_ug_m3=concentration, duration_minutes=60, breathing_rate_m3_per_hr=rate
    )
    higher = base.model_copy(update={"breathing_rate_m3_per_hr": rate * 1.5})
    assert (
        calculate_inhaled_dose(higher).inhaled_dose_ug
        >= calculate_inhaled_dose(base).inhaled_dose_ug
    )


def test_incomplete_cpcb_keeps_subindices_without_valid_overall() -> None:
    result = calculate_cpcb_aqi({"PM2.5": 165, "PM10": 200})
    assert not result.is_valid
    assert len(result.sub_indices) == 2
    assert result.indicative_aqi is not None and result.indicative_aqi > 300
