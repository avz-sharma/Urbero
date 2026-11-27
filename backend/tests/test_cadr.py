"""Unit tests for Room CADR and indoor action engine."""

import pytest
from pydantic import ValidationError

from backend.app.config.constants import DISCLAIMER_INDOOR_PLANTS
from backend.app.exposure.cadr import (
    RoomDimensions,
    RoomIndoorFactors,
    calculate_room_cadr,
)


@pytest.mark.parametrize(
    ("length", "volume", "cadr", "cfm"),
    [(5, 56, 280, 164.8), (6, 67.2, 336, 197.76)],
)
def test_room_result_captures_its_applied_inputs(
    length: float, volume: float, cadr: float, cfm: float
) -> None:
    dimensions = RoomDimensions(length_m=length, width_m=4, height_m=2.8)
    result = calculate_room_cadr(dimensions)
    dimensions.length_m = 10

    payload = result.model_dump()
    assert payload["dimensions"] == {"length_m": length, "width_m": 4, "height_m": 2.8}
    assert payload["factors"] == {
        "has_kitchen_chimney": True,
        "burns_incense_agarbatti": False,
        "has_unsealed_balcony": False,
    }
    assert payload["source_multiplier"] == 1
    assert result.room_volume_m3 == volume
    assert result.required_cadr_m3_per_hr == cadr
    assert result.required_cadr_cfm == cfm


def test_standard_room_cadr() -> None:
    """Test baseline CADR calculation for typical Indian master bedroom."""
    # 5m x 4m x 3m = 60 m³ volume, target 5 ACH -> 300 m³/h
    dims = RoomDimensions(length_m=5.0, width_m=4.0, height_m=3.0)
    factors = RoomIndoorFactors(
        has_kitchen_chimney=True,
        burns_incense_agarbatti=False,
        has_unsealed_balcony=False,
    )
    result = calculate_room_cadr(dims, factors, target_ach=5.0)

    assert result.room_volume_m3 == 60.0
    assert result.target_ach == 5.0
    assert result.required_cadr_m3_per_hr == 300.0
    assert pytest.approx(result.required_cadr_cfm, 0.1) == 176.6  # 300 * 0.5885775
    assert result.plants_footnote == DISCLAIMER_INDOOR_PLANTS


def test_cadr_with_indoor_pollution_sources() -> None:
    """Verify that unvented cooking and agarbatti increase required CADR."""
    dims = RoomDimensions(length_m=4.0, width_m=3.0, height_m=3.0)  # 36 m³
    factors = RoomIndoorFactors(
        has_kitchen_chimney=False,  # +25%
        burns_incense_agarbatti=True,  # +30%
        has_unsealed_balcony=True,
    )
    result = calculate_room_cadr(dims, factors, target_ach=5.0)

    # Base CADR = 36 * 5 = 180 m³/h
    # Multiplier = 1.0 + 0.25 + 0.30 = 1.55
    # Adjusted CADR = 180 * 1.55 = 279 m³/h
    assert result.model_dump()["source_multiplier"] == 1.55
    assert result.required_cadr_m3_per_hr == 279.0
    assert "chimney" in result.sealing_and_source_guidance.lower()
    assert "incense" in result.sealing_and_source_guidance.lower()
    assert "balcony" in result.sealing_and_source_guidance.lower()


def test_invalid_dimensions_raise() -> None:
    """Test negative or zero dimensions raise validation error."""
    with pytest.raises(ValidationError):
        calculate_room_cadr(RoomDimensions(length_m=-4.0, width_m=3.0, height_m=3.0))
