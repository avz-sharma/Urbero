"""Unit tests for household routine optimizer and Smog Episode mode."""

import pytest

from backend.app.config.constants import DISCLAIMER_SMOG_EPISODE
from backend.app.exposure.optimizer import (
    ScheduledActivity,
    optimize_daily_routine,
)


def test_smog_episode_mode_activation() -> None:
    """Verify Smog Episode Mode triggers at AQI > 300 with mandatory N95 & doctor lines."""
    activities = [
        ScheduledActivity(
            id="a1",
            name="Morning Park Walk",
            member_name="Dada Ji (Grandfather)",
            age_group="senior",
            intensity="moderate",
            scheduled_start_hour=7.0,
            scheduled_end_hour=8.0,
            is_outdoor=True,
            is_flexible=True,
        ),
        ScheduledActivity(
            id="a2",
            name="School Bus Commute",
            member_name="Aarav (8yo)",
            age_group="child",
            intensity="light",
            scheduled_start_hour=7.5,
            scheduled_end_hour=8.25,
            is_outdoor=True,
            is_flexible=False,
        ),
    ]

    hourly_pm25 = {7: 240.0, 8: 250.0, 13: 85.0, 14: 90.0}

    # AQI 340 (Very Poor / Severe) triggers Smog Episode Mode
    res = optimize_daily_routine(activities, hourly_pm25, current_aqi=340)

    assert res.smog_episode_active is True
    assert res.smog_episode_advisory == DISCLAIMER_SMOG_EPISODE
    # Mandatory honesty checks:
    assert "fitted N95/FFP2" in res.smog_episode_advisory
    assert "cloth" in res.smog_episode_advisory.lower()
    assert "consult a doctor" in res.smog_episode_advisory.lower()

    # Grandfather's flexible walk shifted indoors
    dada_act = next(a for a in res.activities if a.member_name.startswith("Dada"))
    assert dada_act.is_shifted_indoors is True
    assert dada_act.dose_reduction_ug > 0

    # Aarav's mandatory school trip gets N95 advisory
    aarav_act = next(a for a in res.activities if a.member_name.startswith("Aarav"))
    assert "N95/FFP2" in aarav_act.recommendation_note


def test_clean_air_day_no_alarmism() -> None:
    """Verify clean air day (AQI <= 100) does not trigger alarmism."""
    activities = [
        ScheduledActivity(
            id="a1",
            name="Evening Football Practice",
            member_name="Aarav",
            age_group="child",
            intensity="heavy",
            scheduled_start_hour=17.0,
            scheduled_end_hour=18.5,
            is_outdoor=True,
            is_flexible=True,
        )
    ]
    hourly_pm25 = {17: 35.0, 18: 40.0}

    res = optimize_daily_routine(activities, hourly_pm25, current_aqi=65)

    assert res.clean_air_day is True
    assert res.smog_episode_active is False
    assert "Clean air window today" in res.overall_advisory
    assert "encouraged" in res.overall_advisory.lower()


def test_moderate_day_schedule_shift() -> None:
    """Verify flexible morning jog is shifted to afternoon on moderate/poor AQI day."""
    activities = [
        ScheduledActivity(
            id="a1",
            name="Morning Jog",
            member_name="Rohan",
            age_group="adult",
            intensity="heavy",
            scheduled_start_hour=7.0,
            scheduled_end_hour=8.0,
            is_outdoor=True,
            is_flexible=True,
        )
    ]
    hourly_pm25 = {7: 180.0, 8: 190.0, 13: 75.0, 14: 80.0}

    res = optimize_daily_routine(activities, hourly_pm25, current_aqi=220)

    assert res.smog_episode_active is False
    assert res.clean_air_day is False
    jog = res.activities[0]
    assert jog.is_shifted is True
    assert jog.optimized_start_hour == 13.0
    assert jog.dose_reduction_ug > 0


def test_empty_schedule_keeps_smog_advisory() -> None:
    result = optimize_daily_routine([], {}, current_aqi=350, current_pm25=180)
    assert result.activities == []
    assert result.smog_episode_active
    assert "Add a household activity" in result.overall_advisory


def test_fractional_fixed_schedule_uses_both_hours() -> None:
    activity = ScheduledActivity(
        id="pickup",
        name="School pickup",
        member_name="Parent",
        scheduled_start_hour=7.75,
        scheduled_end_hour=8.25,
        is_flexible=False,
    )
    result = optimize_daily_routine([activity], {7: 80, 8: 120}, current_aqi=160)
    assert result.activities[0].baseline_inhaled_pm25_ug == pytest.approx(60)
    assert result.activities[0].optimized_start_hour == 7.75
