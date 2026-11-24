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


def calculate_data_confidence(inp: ConfidenceInput) -> ConfidenceResult:
    """Calculate Data Confidence (High / Medium / Low) with an auditable explanation.

    Scoring criteria:
    - Distance: < 5km (40 pts), 5-15km (25 pts), > 15km (10 pts)
    - Freshness: < 60m (30 pts), 60-180m (15 pts), > 180m (0 pts)
    - Completeness: >= 4 pollutants with PM (20 pts), 3 with PM (10 pts), < 3 (0 pts)
    - Hardware: Reference-grade regulatory monitor (+10 pts)
    """
    score = 0
    reasons: list[str] = []

    # 1. Proximity score (Max 40)
    if inp.distance_km <= 5.0:
        score += 40
        reasons.append(f"Station is nearby ({inp.distance_km:.1f} km)")
    elif inp.distance_km <= 15.0:
        score += 25
        reasons.append(f"Station is moderately close ({inp.distance_km:.1f} km)")
    else:
        score += 10
        reasons.append(f"Far station ({inp.distance_km:.1f} km)")

    # 2. Reading Freshness (Max 30)
    age_seconds = max(0.0, (inp.fetched_at - inp.observed_at).total_seconds())
    age_minutes = age_seconds / 60.0

    if age_minutes <= 60.0:
        score += 30
        reasons.append(f"fresh reading ({int(age_minutes)} mins ago)")
    elif age_minutes <= 180.0:
        score += 15
        reasons.append(f"moderately aged reading ({int(age_minutes)} mins ago)")
    else:
        reasons.append(f"stale reading ({int(age_minutes // 60)} hours ago)")

    # 3. Parameter Completeness (Max 20)
    has_pm = any(p in {"PM2.5", "PM10"} for p in inp.pollutants_present)
    param_count = len(inp.pollutants_present)

    if param_count >= 4 and has_pm:
        score += 20
        reasons.append(f"{param_count} pollutants tracked including PM")
    elif param_count >= 3 and has_pm:
        score += 10
        reasons.append("basic 3 pollutants available")
    else:
        reasons.append("incomplete pollutant telemetry")

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
