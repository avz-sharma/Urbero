"""Unit tests for station-history diurnal profiler."""

from datetime import UTC, datetime, timedelta

import pytest

from backend.app.aqi.diurnal import (
    HourlyMeasurement,
    compute_diurnal_profile,
)


def test_diurnal_profile_calculation() -> None:
    """Test 24-hour diurnal curve derivation and cleanest window detection."""
    measurements: list[HourlyMeasurement] = []
    base_time = datetime(2026, 11, 20, 0, 0, tzinfo=UTC)

    # Synthetic realistic winter Delhi pattern across 48 hours:
    # High mornings (07:00 ~ 250 µg/m³), low afternoons (14:00 ~ 90 µg/m³), high nights (22:00 ~ 220 µg/m³)
    for day in range(2):
        for h in range(24):
            t = base_time + timedelta(days=day, hours=h)
            if 6 <= h <= 9:
                val = 250.0 + (h * 5.0)
            elif 13 <= h <= 16:
                val = 85.0 + (h * 2.0)
            elif 20 <= h <= 23:
                val = 210.0 + (h * 3.0)
            else:
                val = 160.0
            measurements.append(HourlyMeasurement(observed_at=t, value=val))

    result = compute_diurnal_profile("Anand Vihar, Delhi", measurements)

    assert result.station_name == "Anand Vihar, Delhi"
    assert len(result.hourly_curve) == 24
    assert result.total_samples == 48

    # Cleanest window should be around afternoon (13:00)
    assert 12 <= result.cleanest_window_start <= 14
    assert result.cleanest_window_avg_pm25 < 120.0

    # Peak hours should include morning smog (7-9 AM)
    assert any(h in result.peak_smog_hours for h in [7, 8, 9])
    assert "Cleanest ambient air window" in result.summary_advisory


def test_diurnal_insufficient_samples_raises() -> None:
    """Test error raised when station measurements are fewer than minimum required."""
    now = datetime.now(UTC)
    few_samples = [
        HourlyMeasurement(observed_at=now - timedelta(hours=i), value=100.0) for i in range(5)
    ]
    with pytest.raises(ValueError, match="Insufficient historical data"):
        compute_diurnal_profile("Test Station", few_samples, min_required_samples=12)


def test_missing_hours_are_not_zero_filled() -> None:
    start = datetime(2026, 11, 20, tzinfo=UTC)
    measurements = [
        HourlyMeasurement(observed_at=start + timedelta(days=day, hours=hour), value=75)
        for day in range(3)
        for hour in range(8, 20)
    ]
    result = compute_diurnal_profile("Model history", measurements)
    assert [h.hour for h in result.hourly_curve] == list(range(8, 20))
    assert all(h.avg_pm25 == 75 and h.sample_count == 3 for h in result.hourly_curve)
