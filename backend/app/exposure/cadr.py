"""Pure Room CADR and indoor action engine.

Calculates required Clean Air Delivery Rate (CADR in m³/h and CFM), adjusts for indoor
combustion/cooking sources and envelope leakage, and provides actionable sealing & ventilation guidance.
Indoor plants are strictly demoted to a low-impact scientific footnote.
"""

from typing import Final

from pydantic import BaseModel, Field

from backend.app.config.constants import DISCLAIMER_INDOOR_PLANTS

M3_PER_HR_TO_CFM: Final[float] = 0.5885775


class RoomDimensions(BaseModel):
    """Room physical dimensions in meters."""

    length_m: float = Field(gt=0.0, le=100.0)
    width_m: float = Field(gt=0.0, le=100.0)
    height_m: float = Field(default=2.8, gt=0.0, le=30.0)


class RoomIndoorFactors(BaseModel):
    """Indoor source activities and building envelope leakage factors."""

    has_kitchen_chimney: bool = True
    burns_incense_agarbatti: bool = False
    has_unsealed_balcony: bool = False


class RoomCADRResult(BaseModel):
    """Recommended purifier sizing and indoor air quality actions."""

    dimensions: RoomDimensions
    factors: RoomIndoorFactors
    room_volume_m3: float
    target_ach: float
    source_multiplier: float
    required_cadr_m3_per_hr: float
    required_cadr_cfm: float
    sealing_and_source_guidance: str
    ventilation_recommendation: str
    plants_footnote: str = DISCLAIMER_INDOOR_PLANTS


def calculate_room_cadr(
    dimensions: RoomDimensions,
    factors: RoomIndoorFactors | None = None,
    target_ach: float = 5.0,
) -> RoomCADRResult:
    """Calculate required room purifier CADR and generate practical indoor actions."""
    if dimensions.length_m <= 0 or dimensions.width_m <= 0 or dimensions.height_m <= 0:
        raise ValueError("Dimensions must be positive nonzero numbers.")
    if target_ach <= 0:
        raise ValueError("Target ACH must be positive.")

    factors = factors or RoomIndoorFactors()
    volume_m3 = round(dimensions.length_m * dimensions.width_m * dimensions.height_m, 2)

    # Base CADR = Volume (m³) * Target ACH (Air Changes per Hour)
    base_cadr = volume_m3 * target_ach

    # Indoor emission penalties
    adjustment_multiplier = 1.0
    guidance_notes: list[str] = []

    if not factors.has_kitchen_chimney:
        adjustment_multiplier += 0.25
        guidance_notes.append(
            "Install or service kitchen exhaust/chimney; sizing includes an illustrative 25% source allowance, not a measured concentration increase."
        )

    if factors.burns_incense_agarbatti:
        adjustment_multiplier += 0.30
        guidance_notes.append(
            "Extinguish incense/agarbatti/dhoop during smog season; smoldering produces dense ultrafine particulates."
        )

    if factors.has_unsealed_balcony:
        guidance_notes.append(
            "Apply adhesive foam weatherstripping and door sweeps to balcony and main doors to seal infiltration gaps."
        )

    if not guidance_notes:
        guidance_notes.append(
            "Good envelope control: maintain closed windows during smog peaks and operate purifier on auto/medium."
        )

    adjusted_cadr = round(base_cadr * adjustment_multiplier, 2)
    cadr_cfm = round(adjusted_cadr * M3_PER_HR_TO_CFM, 2)

    vent_guidance = (
        "Timing ventilation: ventilate briefly when verified outdoor pollution is lower than indoors. "
        "Use available local history rather than assuming a fixed clean afternoon window; control cooking sources first."
    )

    return RoomCADRResult(
        dimensions=dimensions.model_copy(),
        factors=factors.model_copy(),
        room_volume_m3=volume_m3,
        target_ach=target_ach,
        source_multiplier=adjustment_multiplier,
        required_cadr_m3_per_hr=adjusted_cadr,
        required_cadr_cfm=cadr_cfm,
        sealing_and_source_guidance=" ".join(guidance_notes),
        ventilation_recommendation=vent_guidance,
    )
