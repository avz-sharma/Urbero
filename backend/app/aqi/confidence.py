"""Pure Data Confidence badge scorer.

Evaluates air quality telemetry reliability (High / Medium / Low) based on monitoring station
proximity (distance_km), measurement freshness (observed_at vs fetched_at), and sensor completeness.
Zero I/O.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ConfidenceInput(BaseModel):
    """Input parameters for evaluating sensor data confidence."""

    distance_km: float = Field(ge=0.0)
    observed_at: datetime
    fetched_at: datetime
    pollutants_present: list[str] = Field(default_factory=list)
    is_reference_grade: bool | None = None
    is_modelled: bool = False


class ConfidenceResult(BaseModel):
    """Data confidence rating and plain-language justification."""

    level: Literal["High", "Medium", "Low"]
    score_percent: int
    reason: str


def _distance_score(distance_km: float) -> tuple[int, str]:
    if distance_km <= 5.0:
        return 40, f"Station is nearby ({distance_km:.1f} km)"
    if distance_km <= 15.0:
        return 25, f"Station is moderately close ({distance_km:.1f} km)"
    return 10, f"Far station ({distance_km:.1f} km)"


def _freshness_score(observed_at: datetime, fetched_at: datetime) -> tuple[int, str]:
    age_minutes = max(0.0, (fetched_at - observed_at).total_seconds()) / 60.0
    if age_minutes <= 60.0:
        return 30, f"fresh reading ({int(age_minutes)} mins ago)"
    if age_minutes <= 180.0:
        return 15, f"moderately aged reading ({int(age_minutes)} mins ago)"
    return 0, f"stale reading ({int(age_minutes // 60)} hours ago)"


def _completeness_score(pollutants_present: list[str]) -> tuple[int, str]:
    count = len(pollutants_present)
    if count < 3 or not {"PM2.5", "PM10"}.intersection(pollutants_present):
        return 0, "incomplete pollutant telemetry"
    if count == 3:
        return 10, "basic 3 pollutants available"
    return 20, f"{count} pollutants tracked including PM"


def calculate_data_confidence(inp: ConfidenceInput) -> ConfidenceResult:
    """Calculate Data Confidence (High / Medium / Low) with an auditable explanation.

    Scoring criteria:
    - Distance: < 5km (40 pts), 5-15km (25 pts), > 15km (10 pts)
    - Freshness: < 60m (30 pts), 60-180m (15 pts), > 180m (0 pts)
    - Completeness: >= 4 pollutants with PM (20 pts), 3 with PM (10 pts), < 3 (0 pts)
    - Hardware: Reference-grade regulatory monitor (+10 pts)
    """
    distance_score, distance_reason = _distance_score(inp.distance_km)
    freshness_score, freshness_reason = _freshness_score(inp.observed_at, inp.fetched_at)
    completeness_score, completeness_reason = _completeness_score(inp.pollutants_present)
    score = distance_score + freshness_score + completeness_score
    reasons = [distance_reason, freshness_reason, completeness_reason]

    # 4. Sensor Classification (Max 10)
    if inp.is_reference_grade is True:
        score += 10
        reasons.append("official CPCB reference-grade regulatory monitor")
    elif inp.is_reference_grade is False:
        reasons.append("low-cost sensor")

    # Determine badge tier
    if score >= 75:
        level: Literal["High", "Medium", "Low"] = "High"
    elif score >= 50:
        level = "Medium"
    else:
        level = "Low"

    full_reason = "; ".join(reasons) + "."
    if inp.is_modelled:
        return ConfidenceResult(
            level="Low",
            score_percent=min(score, 40),
            reason="CAMS model estimate, not a ground-station measurement; distance is to the model grid, not a station. "
            + full_reason.replace("Station is nearby", "Grid centre is nearby")
            .replace("Station is moderately close", "Grid centre is moderately close")
            .replace("Far station", "Far grid centre"),
        )

    return ConfidenceResult(
        level=level,
        score_percent=score,
        reason=full_reason,
    )
