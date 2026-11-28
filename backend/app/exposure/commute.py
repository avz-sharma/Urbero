"""Pure Planet vs. Lungs commute mode comparator.

Quantifies personal inhaled PM2.5 dose alongside tailpipe/grid CO2 emissions across travel modes.
Highlights critical trade-offs: during severe smog episodes, active roadside modes (cycling/walking)
eliminate CO2 emissions but dramatically increase personal lung exposure due to elevated ventilation rates.
Zero I/O.
"""

from typing import Final

from pydantic import BaseModel

from backend.app.config.constants import (
    COMMUTE_CO2_GRAMS_PER_KM,
    COMMUTE_EXPOSURE_FACTORS,
)

# Standard urban commuter speeds in Indian metros (km/h)
COMMUTE_SPEEDS_KMH: Final[dict[str, float]] = {
    "walking": 4.5,
    "cycling": 14.0,
    "metro": 32.0,
    "electric_2w": 25.0,
    "bus_public": 16.0,
    "petrol_2w": 28.0,
    "auto_rickshaw": 20.0,
    "petrol_car_solo": 22.0,
}

# Breathing rates (m³/h) by commute mode
COMMUTE_BREATHING_RATES: Final[dict[str, float]] = {
    "walking": 1.20,  # moderate walking
    "cycling": 2.10,  # heavy aerobic exertion
    "metro": 0.60,  # seated / standing light
    "electric_2w": 0.70,  # seated motorized
    "bus_public": 0.65,
    "petrol_2w": 0.70,
    "auto_rickshaw": 0.65,
    "petrol_car_solo": 0.60,
}

MODE_DISPLAY_LABELS: Final[dict[str, str]] = {
    "walking": "Walking (Pavement)",
    "cycling": "Bicycle (Roadway)",
    "metro": "Metro Train (Air-conditioned)",
    "electric_2w": "Electric Scooter (EV)",
    "bus_public": "Public Bus (Transit)",
    "petrol_2w": "Motorcycle / Scooter",
    "auto_rickshaw": "Auto-Rickshaw (CNG 3-Wheeler)",
    "petrol_car_solo": "Private Car (Solo, AC Recirculation)",
}


class CommuteModeComparison(BaseModel):
    """Side-by-side personal lung health vs planetary climate impact metrics."""

    mode: str
    label: str
    distance_km: float
    duration_minutes: float
    tailpipe_co2_grams: float
    personal_inhaled_pm25_ug: float
    exposure_multiplier: float
    planet_vs_lungs_note: str


def compare_commute_modes(
    distance_km: float,
    ambient_pm25_ug_m3: float,
    target_modes: list[str] | None = None,
    *,
    include_metro: bool = True,
) -> list[CommuteModeComparison]:
    """Calculate and compare personal inhaled PM2.5 dose and CO2 emissions across modes."""
    if distance_km <= 0:
        raise ValueError(f"Distance must be positive: {distance_km}")
    if ambient_pm25_ug_m3 < 0:
        raise ValueError(f"Ambient PM2.5 cannot be negative: {ambient_pm25_ug_m3}")

    modes = (
        target_modes
        if target_modes is not None
        else [
            *(["metro"] if include_metro else []),
            "cycling",
            "walking",
            "bus_public",
            "auto_rickshaw",
            "petrol_2w",
            "petrol_car_solo",
        ]
    )

    results: list[CommuteModeComparison] = []

    for mode in modes:
        if mode not in COMMUTE_SPEEDS_KMH:
            continue

        speed = COMMUTE_SPEEDS_KMH[mode]
        duration_hours = distance_km / speed
        duration_mins = round(duration_hours * 60.0, 1)

        # Carbon calculation
        co2_factor = COMMUTE_CO2_GRAMS_PER_KM.get(mode, 0.0)
        co2_total = round(distance_km * co2_factor, 1)

        # Inhaled PM2.5 calculation
        exposure_mult = COMMUTE_EXPOSURE_FACTORS.get(mode, 1.0)
        breathing_rate = COMMUTE_BREATHING_RATES.get(mode, 0.60)
        inhaled_ug = round(ambient_pm25_ug_m3 * exposure_mult * breathing_rate * duration_hours, 1)

        # Trade-off narrative synthesis
        if mode == "metro":
            trade_off = (
                f"Optimal Win-Win: Estimated {inhaled_ug} µg inhaled PM2.5 and "
                f"{co2_total} g CO2 from grid electricity for this trip."
            )
        elif mode in {"cycling", "walking"}:
            if ambient_pm25_ug_m3 > 120.0:  # Very Poor / Severe
                trade_off = (
                    "Planet vs. Lungs Conflict: 0g CO2 benefits the planet, but elevated respiration and direct "
                    f"roadway proximity contribute to an estimated {inhaled_ug} µg inhaled PM2.5. "
                    "Avoid active roadside commuting during severe smog."
                )
            else:
                trade_off = (
                    "Zero tailpipe emissions and moderate personal dose in acceptable ambient air."
                )
        elif mode == "petrol_car_solo":
            trade_off = (
                "Lungs protected inside AC cabin recirculation, but generates the highest individual carbon footprint "
                f"({co2_total}g CO2)."
            )
        elif mode == "auto_rickshaw":
            trade_off = "Direct exposure to adjacent tailpipes in open cabin with moderate transit emissions."
        else:
            trade_off = (
                f"Standard transit mode: {co2_total}g CO2 with {inhaled_ug} µg personal exposure."
            )

        results.append(
            CommuteModeComparison(
                mode=mode,
                label=MODE_DISPLAY_LABELS.get(mode, mode.title()),
                distance_km=distance_km,
                duration_minutes=duration_mins,
                tailpipe_co2_grams=co2_total,
                personal_inhaled_pm25_ug=inhaled_ug,
                exposure_multiplier=exposure_mult,
                planet_vs_lungs_note=trade_off,
            )
        )

    return results
