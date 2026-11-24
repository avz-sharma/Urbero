"""Unit and golden-value regression tests for CPCB National AQI calculator."""

import pytest

from backend.app.aqi.cpcb import (
    calculate_cpcb_aqi,
    calculate_sub_index,
    get_aqi_category,
)


def test_sub_index_boundaries_pm25() -> None:
    """Test CPCB PM2.5 sub-index breakpoints and boundary edges."""
    # Good band: 0 - 30 -> 0 - 50
    assert calculate_sub_index("PM2.5", 0.0) == 0
    assert calculate_sub_index("PM2.5", 15.0) == 25
    assert calculate_sub_index("PM2.5", 30.0) == 50

    # Satisfactory boundary edge: 31 - 60 -> 51 - 100
    assert calculate_sub_index("PM2.5", 31.0) == 51
    # Golden value from CPCB manual: Cp = 45 µg/m³ -> AQI 75
    assert calculate_sub_index("PM2.5", 45.0) == 75
    assert calculate_sub_index("PM2.5", 60.0) == 100

    # Moderate boundary edge: 61 - 90 -> 101 - 200
    assert calculate_sub_index("PM2.5", 61.0) == 101
    assert calculate_sub_index("PM2.5", 90.0) == 200

    # Poor boundary edge: 91 - 120 -> 201 - 300
    assert calculate_sub_index("PM2.5", 91.0) == 201
    assert calculate_sub_index("PM2.5", 120.0) == 300

    # Very Poor boundary edge: 121 - 250 -> 301 - 400
    assert calculate_sub_index("PM2.5", 121.0) == 301
    assert calculate_sub_index("PM2.5", 250.0) == 400

    # Severe boundary: > 250 -> 401 - 500
    assert calculate_sub_index("PM2.5", 251.0) == 401
    assert calculate_sub_index("PM2.5", 500.0) == 500


def test_sub_index_co_mg_m3() -> None:
    """Verify CO uses mg/m³ breakpoints."""
    # Good: 0 - 1.0 mg/m³ -> 0 - 50
    assert calculate_sub_index("CO", 0.5) == 25
    assert calculate_sub_index("CO", 1.0) == 50

    # Satisfactory: 1.1 - 2.0 mg/m³ -> 51 - 100
    assert calculate_sub_index("CO", 1.1) == 51
    assert calculate_sub_index("CO", 2.0) == 100

    # Moderate: 2.1 - 10.0 mg/m³ -> 101 - 200
    assert calculate_sub_index("CO", 6.05) in {150, 151}


def test_negative_and_invalid_pollutant() -> None:
    """Verify error handling for negative and unknown pollutants."""
    with pytest.raises(ValueError, match="negative"):
        calculate_sub_index("PM2.5", -5.0)

    with pytest.raises(ValueError, match="Unknown pollutant"):
        calculate_sub_index("UNOBTAINIUM", 50.0)


def test_get_aqi_category_and_colors() -> None:
    """Verify AQI categories and color code mappings."""
    cat, color = get_aqi_category(25)
    assert cat == "Good" and color == "#00B050"

    cat, color = get_aqi_category(80)
    assert cat == "Satisfactory" and color == "#92D050"

    cat, color = get_aqi_category(150)
    assert cat == "Moderate" and color == "#FFFF00"

    cat, color = get_aqi_category(250)
    assert cat == "Poor" and color == "#FF9900"

    cat, color = get_aqi_category(350)
    assert cat == "Very Poor" and color == "#FF0000"

    cat, color = get_aqi_category(450)
    assert cat == "Severe" and color == "#C00000"


def test_cpcb_clamped_category_and_bounds() -> None:
    """Test get_aqi_category clamping above 500 and invalid pollutant filtering."""
    cat, col = get_aqi_category(650)
    assert cat == "Severe" and col == "#C00000"

    cat, col = get_aqi_category(-10)
    assert cat == "Good" and col == "#00B050"

    # Readings with unknown pollutants are filtered
    res = calculate_cpcb_aqi(
        {
            "PM2.5": 45.0,
            "PM10": 70.0,
            "NO2": 40.0,
            "UNKNOWN": 999.0,
        }
    )
    assert res.is_valid
    assert len(res.sub_indices) == 3
    """Test CPCB minimum 3 pollutants rule with mandatory PM parameter."""
    # Case 1: Only 2 pollutants (PM2.5, NO2) -> Invalid
    res_2 = calculate_cpcb_aqi({"PM2.5": 75.0, "NO2": 50.0})
    assert not res_2.is_valid
    assert "minimum 3 pollutants" in res_2.validation_message.lower()

    # Case 2: 3 pollutants but NO particulate matter (NO2, SO2, CO) -> Invalid
    res_no_pm = calculate_cpcb_aqi({"NO2": 50.0, "SO2": 30.0, "CO": 1.2})
    assert not res_no_pm.is_valid
    assert "particulate" in res_no_pm.validation_message.lower()

    # Case 3: 3 pollutants with PM2.5 -> Valid
    res_valid = calculate_cpcb_aqi({"PM2.5": 75.0, "NO2": 50.0, "CO": 1.2})
    assert res_valid.is_valid
    assert res_valid.overall_aqi > 0
    assert res_valid.dominant_pollutant == "PM2.5"

    # Case 4: Dominant pollutant selection (maximum sub-index)
    res_multi = calculate_cpcb_aqi(
        {
            "PM2.5": 45.0,  # sub-index 75
            "PM10": 280.0,  # sub-index in Poor (201-300)
            "NO2": 60.0,  # sub-index in Satisfactory
            "CO": 0.8,  # sub-index in Good
        }
    )
    assert res_multi.is_valid
    assert res_multi.dominant_pollutant == "PM10"
    assert res_multi.category == "Poor"
