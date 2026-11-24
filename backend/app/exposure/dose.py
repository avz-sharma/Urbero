"""Pure inhaled PM2.5 dose and Berkeley Earth cigarette equivalence calculator.

Zero I/O, deterministic physiological exposure model based on US EPA / WHO breathing rates
and Berkeley Earth particle-mass cigarette heuristics.
"""

from pydantic import BaseModel, Field

from backend.app.config.constants import (
    BERKELEY_EARTH_INHALED_UG_PER_CIGARETTE,
    DISCLAIMER_CIGARETTE_HEURISTIC,
    DISCLAIMER_EXPOSURE_BASELINES,
    INDIA_NAAQS_PM25_24HR_LIMIT,
    WHO_2021_PM25_24HR_GUIDELINE,
)


class DoseCalculationInput(BaseModel):
    """Input parameters for personal PM2.5 inhaled dose computation."""

    pm25_concentration_ug_m3: float
    duration_minutes: float
    breathing_rate_m3_per_hr: float
    infiltration_factor: float = Field(default=1.0, ge=0.0, le=1.0)
    purifier_efficiency: float = Field(default=0.0, ge=0.0, le=1.0)


class DoseCalculationResult(BaseModel):
    """Computed personal exposure metrics with mandatory transparency disclaimers."""

    duration_hours: float
    indoor_effective_concentration_ug_m3: float
    inhaled_dose_ug: float
    cigarette_equivalent: float
    who_24hr_reference_dose_ug: float
    naaqs_24hr_reference_dose_ug: float
    disclaimer_cigarette: str = DISCLAIMER_CIGARETTE_HEURISTIC
    disclaimer_baselines: str = DISCLAIMER_EXPOSURE_BASELINES


def calculate_inhaled_dose(inp: DoseCalculationInput) -> DoseCalculationResult:
    """Calculate inhaled PM2.5 mass in micrograms and cigarette equivalence.

    Formula:
      effective_conc = outdoor_conc * infiltration_factor * (1.0 - purifier_efficiency)
      inhaled_dose = effective_conc * breathing_rate * duration_hours
    """
    if inp.pm25_concentration_ug_m3 < 0.0:
        raise ValueError(f"Concentration cannot be negative: {inp.pm25_concentration_ug_m3}")
    if inp.duration_minutes < 0.0:
        raise ValueError(f"Duration cannot be negative: {inp.duration_minutes}")
    if inp.breathing_rate_m3_per_hr <= 0.0:
        raise ValueError(f"Breathing rate must be positive: {inp.breathing_rate_m3_per_hr}")

    duration_hours = inp.duration_minutes / 60.0

    # Indoor penetration & active filtration
    effective_factor = inp.infiltration_factor * (1.0 - inp.purifier_efficiency)
    effective_conc = inp.pm25_concentration_ug_m3 * effective_factor

    # Inhaled particulate mass in µg
    inhaled_ug = effective_conc * inp.breathing_rate_m3_per_hr * duration_hours

    # Berkeley Earth cigarette equivalence heuristic (~396 µg inhaled PM2.5 per cigarette)
    cigarette_eq = inhaled_ug / BERKELEY_EARTH_INHALED_UG_PER_CIGARETTE

    # 24-hour regulatory baselines for context
    who_ref_ug = WHO_2021_PM25_24HR_GUIDELINE * inp.breathing_rate_m3_per_hr * 24.0
    naaqs_ref_ug = INDIA_NAAQS_PM25_24HR_LIMIT * inp.breathing_rate_m3_per_hr * 24.0

    return DoseCalculationResult(
        duration_hours=duration_hours,
        indoor_effective_concentration_ug_m3=effective_conc,
        inhaled_dose_ug=inhaled_ug,
        cigarette_equivalent=cigarette_eq,
        who_24hr_reference_dose_ug=who_ref_ug,
        naaqs_24hr_reference_dose_ug=naaqs_ref_ug,
    )
