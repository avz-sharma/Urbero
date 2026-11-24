"""Property-based regression tests using Hypothesis."""

from hypothesis import given
from hypothesis import strategies as st

from backend.app.aqi.cpcb import calculate_sub_index
from backend.app.exposure.cadr import (
    RoomDimensions,
    RoomIndoorFactors,
    calculate_room_cadr,
)
from backend.app.exposure.dose import (
    DoseCalculationInput,
    calculate_inhaled_dose,
)


@given(
    st.sampled_from(["PM2.5", "PM10", "NO2", "O3", "SO2", "NH3"]),
    st.floats(min_value=0.0, max_value=500.0),
    st.floats(min_value=0.0, max_value=500.0),
)
def test_sub_index_monotonicity(pollutant: str, c1: float, c2: float) -> None:
    """Hypothesis property: higher pollutant concentration must never yield lower AQI sub-index."""
    low, high = sorted([c1, c2])
    sub_low = calculate_sub_index(pollutant, low)
    sub_high = calculate_sub_index(pollutant, high)
    assert sub_low <= sub_high, (
        f"Monotonicity failed for {pollutant}: {low} -> {sub_low}, {high} -> {sub_high}"
    )


@given(
    st.floats(min_value=0.0, max_value=1000.0),
    st.floats(min_value=0.1, max_value=3.0),
    st.floats(min_value=1.0, max_value=600.0),
)
def test_dose_monotonicity(conc: float, rate: float, duration: float) -> None:
    """Hypothesis property: increasing concentration or breathing rate never decreases dose."""
    res1 = calculate_inhaled_dose(
        DoseCalculationInput(
            pm25_concentration_ug_m3=conc,
            breathing_rate_m3_per_hr=rate,
            duration_minutes=duration,
        )
    )
    res2 = calculate_inhaled_dose(
        DoseCalculationInput(
            pm25_concentration_ug_m3=conc * 1.5,
            breathing_rate_m3_per_hr=rate,
            duration_minutes=duration,
        )
    )
    assert res2.inhaled_dose_ug >= res1.inhaled_dose_ug


@given(
    st.floats(min_value=1.0, max_value=20.0),
    st.floats(min_value=1.0, max_value=20.0),
    st.floats(min_value=2.0, max_value=5.0),
    st.floats(min_value=2.0, max_value=8.0),
)
def test_cadr_monotonicity(length: float, width: float, height: float, ach: float) -> None:
    """Hypothesis property: larger room volume or higher ACH never lowers required CADR."""
    dims = RoomDimensions(length_m=length, width_m=width, height_m=height)
    factors = RoomIndoorFactors()
    res = calculate_room_cadr(dims, factors, target_ach=ach)
    assert res.room_volume_m3 > 0
    assert res.required_cadr_m3_per_hr >= round(res.room_volume_m3 * ach, 2) - 0.01
