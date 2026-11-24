"""Unit tests for Data Confidence badge scorer."""

from datetime import UTC, datetime, timedelta

from backend.app.aqi.confidence import (
    ConfidenceInput,
    calculate_data_confidence,
)


def test_high_confidence_reading() -> None:
    """Verify High confidence criteria: close distance, fresh reading, reference sensor, complete data."""
    now = datetime.now(UTC)
    inp = ConfidenceInput(
        distance_km=3.5,
        observed_at=now - timedelta(minutes=15),
        fetched_at=now,
        pollutants_present=["PM2.5", "PM10", "NO2", "CO", "SO2"],
        is_reference_grade=True,
    )
    result = calculate_data_confidence(inp)
    assert result.level == "High"
    assert "3.5 km" in result.reason
    assert "reference-grade" in result.reason.lower()


def test_medium_confidence_reading() -> None:
    """Verify Medium confidence when distance or age is moderate."""
    now = datetime.now(UTC)
    inp = ConfidenceInput(
        distance_km=11.0,  # moderate distance
        observed_at=now - timedelta(minutes=75),  # > 1 hour
        fetched_at=now,
        pollutants_present=["PM2.5", "PM10", "NO2"],
        is_reference_grade=False,
    )
    result = calculate_data_confidence(inp)
    assert result.level == "Medium"
    assert "11.0 km" in result.reason


def test_low_confidence_reading() -> None:
    """Verify Low confidence when station is far or reading is stale."""
    now = datetime.now(UTC)
    inp = ConfidenceInput(
        distance_km=28.0,  # far station
        observed_at=now - timedelta(hours=5),  # stale > 3 hours
        fetched_at=now,
        pollutants_present=["PM2.5"],
        is_reference_grade=None,
    )
    result = calculate_data_confidence(inp)
    assert result.level == "Low"
    assert "far station" in result.reason.lower() or "stale" in result.reason.lower()
