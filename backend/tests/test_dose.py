"""Unit tests for inhaled PM2.5 dose and Berkeley Earth cigarette equivalence."""

import pytest

from backend.app.config.constants import (
    BERKELEY_EARTH_INHALED_UG_PER_CIGARETTE,
    DISCLAIMER_CIGARETTE_HEURISTIC,
    DISCLAIMER_EXPOSURE_BASELINES,
)
from backend.app.exposure.dose import (
    DoseCalculationInput,
    calculate_inhaled_dose,
)


def test_basic_dose_calculation() -> None:
    """Test standard outdoor walking inhaled dose."""
    # 100 µg/m³, adult moderate walking (1.2 m³/h), 1 hour (60 min), no purifier (eff 0), infiltration 1.0
    inp = DoseCalculationInput(
        pm25_concentration_ug_m3=100.0,
        duration_minutes=60.0,
        breathing_rate_m3_per_hr=1.2,
        infiltration_factor=1.0,
        purifier_efficiency=0.0,
    )
    result = calculate_inhaled_dose(inp)

    # Inhaled dose = 100 * 1.2 * 1.0 * 1.0 * 1.0 = 120.0 µg
    assert pytest.approx(result.inhaled_dose_ug, 0.01) == 120.0
    assert (
        pytest.approx(result.cigarette_equivalent, abs=0.01)
        == 120.0 / BERKELEY_EARTH_INHALED_UG_PER_CIGARETTE
    )
    assert result.disclaimer_cigarette == DISCLAIMER_CIGARETTE_HEURISTIC
    assert result.disclaimer_baselines == DISCLAIMER_EXPOSURE_BASELINES


def test_indoor_purifier_reduction() -> None:
    """Test that HEPA air purifier reduces inhaled dose according to efficiency."""
    # Outdoor 200 µg/m³, closed windows (0.55 infiltration), HEPA active (0.85 efficiency)
    inp = DoseCalculationInput(
        pm25_concentration_ug_m3=200.0,
        duration_minutes=120.0,  # 2 hours
        breathing_rate_m3_per_hr=0.6,  # adult sedentary
        infiltration_factor=0.55,
        purifier_efficiency=0.85,
    )
    result = calculate_inhaled_dose(inp)

    # Indoor concentration = 200 * 0.55 * (1 - 0.85) = 16.5 µg/m³
    # Inhaled mass = 16.5 * 0.6 * 2.0 = 19.8 µg
    assert pytest.approx(result.indoor_effective_concentration_ug_m3, 0.01) == 16.5
    assert pytest.approx(result.inhaled_dose_ug, 0.01) == 19.8


def test_dose_negative_inputs_raise() -> None:
    """Test validation errors on negative concentrations or durations."""
    with pytest.raises(ValueError, match="Concentration cannot be negative"):
        calculate_inhaled_dose(
            DoseCalculationInput(
                pm25_concentration_ug_m3=-10.0,
                duration_minutes=60.0,
                breathing_rate_m3_per_hr=1.0,
            )
        )

    with pytest.raises(ValueError, match="Duration cannot be negative"):
        calculate_inhaled_dose(
            DoseCalculationInput(
                pm25_concentration_ug_m3=50.0,
                duration_minutes=-15.0,
                breathing_rate_m3_per_hr=1.0,
            )
        )
