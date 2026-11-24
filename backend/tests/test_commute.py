"""Unit tests for Planet vs. Lungs commute mode comparator."""

import pytest

from backend.app.exposure.commute import compare_commute_modes


def test_planet_vs_lungs_severe_smog() -> None:
    """Verify that during severe smog, cycling eliminates CO2 but increases inhaled PM2.5."""
    distance_km = 12.0
    ambient_pm25 = 220.0  # Very Poor / Severe smog episode

    results = compare_commute_modes(distance_km, ambient_pm25)
    modes_by_name = {r.mode: r for r in results}

    assert "cycling" in modes_by_name
    assert "metro" in modes_by_name
    assert "petrol_car_solo" in modes_by_name

    cycling = modes_by_name["cycling"]
    metro = modes_by_name["metro"]
    car = modes_by_name["petrol_car_solo"]

    # 1. Carbon footprint: Cycling is 0g CO2, Metro is low, Car is highest
    assert cycling.tailpipe_co2_grams == 0.0
    assert metro.tailpipe_co2_grams < car.tailpipe_co2_grams
    assert car.tailpipe_co2_grams == 12.0 * 160.0

    # 2. Personal inhaled dose: Cycling has significantly HIGHER inhaled dose than Metro or Car
    assert cycling.personal_inhaled_pm25_ug > metro.personal_inhaled_pm25_ug
    assert cycling.personal_inhaled_pm25_ug > car.personal_inhaled_pm25_ug

    # 3. Planet vs Lungs advisory note exists for active mode
    assert "Planet vs. Lungs Conflict" in cycling.planet_vs_lungs_note
    assert "Optimal Win-Win" in metro.planet_vs_lungs_note


def test_commute_invalid_inputs_raise() -> None:
    """Test validation errors on negative distances or pollutant levels."""
    with pytest.raises(ValueError, match="Distance must be positive"):
        compare_commute_modes(distance_km=-5.0, ambient_pm25_ug_m3=100.0)

    with pytest.raises(ValueError, match="Ambient PM2.5 cannot be negative"):
        compare_commute_modes(distance_km=10.0, ambient_pm25_ug_m3=-20.0)
