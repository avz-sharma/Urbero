"""Pure CPCB National AQI calculator for Indian cities.

Zero I/O, deterministic linear breakpoint interpolation adhering strictly to
CPCB 2014 specifications (never US EPA). Enforces minimum 3-pollutant rule with mandatory PM parameter.
"""

from math import isfinite

from pydantic import BaseModel, Field

from backend.app.config.constants import (
    CPCB_AQI_CATEGORIES,
    CPCB_BREAKPOINTS,
    MIN_VALID_POLLUTANTS_COUNT,
    PM_POLLUTANTS,
)


class SubIndexItem(BaseModel):
    """Sub-index for an individual air pollutant."""

    pollutant: str
    concentration: float
    unit: str
    sub_index: int
    category: str
    color_code: str


class CPCBAQIResult(BaseModel):
    """Aggregated CPCB AQI result with multi-pollutant compliance status."""

    overall_aqi: int = 0
    dominant_pollutant: str = ""
    category: str = "Unknown"
    color_code: str = "#808080"
    sub_indices: list[SubIndexItem] = Field(default_factory=list)
    is_valid: bool = False
    validation_message: str = ""
    indicative_aqi: int | None = None


def get_aqi_category(aqi: int) -> tuple[str, str]:
    """Map an AQI integer to its official CPCB category name and color code."""
    clamped_aqi = max(0, min(500, aqi))
    for low, high, name, color in CPCB_AQI_CATEGORIES:
        if low <= clamped_aqi <= high:
            return name, color
    return "Severe", "#C00000"


def calculate_sub_index(pollutant: str, concentration: float) -> int:
    """Calculate sub-index for a given pollutant concentration using CPCB breakpoints.

    Formula: Ip = ((I_Hi - I_Lo) / (BP_Hi - BP_Lo)) * (Cp - BP_Lo) + I_Lo
    Provides continuous monotonic transition across breakpoint boundaries.
    """
    if not isfinite(concentration) or concentration < 0.0:
        raise ValueError(f"Concentration cannot be negative: {concentration}")

    if pollutant not in CPCB_BREAKPOINTS:
        raise ValueError(f"Unknown pollutant for CPCB calculation: {pollutant}")

    breakpoints = CPCB_BREAKPOINTS[pollutant]

    # Check each breakpoint range
    for idx, bp in enumerate(breakpoints):
        c_low = bp["c_low"]
        c_high = bp["c_high"]
        i_low = bp["aqi_low"]
        i_high = bp["aqi_high"]

        # Exact match within breakpoint range
        if c_low <= concentration <= c_high:
            delta_c = c_high - c_low
            if delta_c == 0:
                return i_low
            sub_index = ((i_high - i_low) / delta_c) * (concentration - c_low) + i_low
            return int(round(sub_index + 1e-9))

        # Check gap between previous band high and current band low (e.g., 30.0 < c < 31.0)
        if idx > 0:
            prev_bp = breakpoints[idx - 1]
            prev_c_high = prev_bp["c_high"]
            prev_i_high = prev_bp["aqi_high"]
            if prev_c_high < concentration < c_low:
                # Monotonic bridge across integer breakpoint gap
                gap_c = c_low - prev_c_high
                gap_i = i_low - prev_i_high
                sub_index = prev_i_high + (gap_i / gap_c) * (concentration - prev_c_high)
                return int(round(sub_index + 1e-9))

    # Concentration exceeds highest tabulated breakpoint: cap at 500 (Severe)
    return 500


def calculate_cpcb_aqi(readings: dict[str, float]) -> CPCBAQIResult:
    """Calculate overall CPCB AQI from a dict of pollutant concentrations.

    Enforces CPCB rules:
    1. Minimum 3 valid pollutants.
    2. At least one must be a particulate parameter (PM2.5 or PM10).
    3. AQI = max(sub-indices). Dominant pollutant = pollutant with max sub-index.
    """
    # Filter known pollutants with non-negative readings
    valid_readings: dict[str, float] = {}
    for p, val in readings.items():
        if p in CPCB_BREAKPOINTS and isfinite(val) and val >= 0.0:
            valid_readings[p] = val

    # Compute sub-indices
    sub_indices: list[SubIndexItem] = []
    max_sub_index = -1
    dominant_pollutant = ""

    for pollutant, conc in valid_readings.items():
        sub = calculate_sub_index(pollutant, conc)
        cat, col = get_aqi_category(sub)
        unit = "mg/m³" if pollutant == "CO" else "µg/m³"
        sub_indices.append(
            SubIndexItem(
                pollutant=pollutant,
                concentration=conc,
                unit=unit,
                sub_index=sub,
                category=cat,
                color_code=col,
            )
        )
        if sub > max_sub_index:
            max_sub_index = sub
            dominant_pollutant = pollutant

    # Expose available PM sub-indices without publishing an invalid overall CPCB AQI.
    if len(valid_readings) < MIN_VALID_POLLUTANTS_COUNT:
        return CPCBAQIResult(
            sub_indices=sub_indices,
            indicative_aqi=max_sub_index if has_pm_reading(valid_readings) else None,
            validation_message=f"CPCB requires a minimum 3 pollutants for valid AQI publication. Found: {len(valid_readings)}",
        )
    if not has_pm_reading(valid_readings):
        return CPCBAQIResult(
            sub_indices=sub_indices,
            validation_message="CPCB requires at least one particulate matter pollutant (PM2.5 or PM10) for valid AQI.",
        )

    overall_cat, overall_col = get_aqi_category(max_sub_index)

    return CPCBAQIResult(
        overall_aqi=max_sub_index,
        dominant_pollutant=dominant_pollutant,
        category=overall_cat,
        color_code=overall_col,
        sub_indices=sub_indices,
        is_valid=True,
        validation_message="Valid CPCB AQI computed.",
    )


def has_pm_reading(readings: dict[str, float]) -> bool:
    return any(p in PM_POLLUTANTS for p in readings)
