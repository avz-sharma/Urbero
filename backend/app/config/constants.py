"""Urbero scientific, physiological, and regulatory domain constants.

Authoritative citations and verification status are pinned inline for all parameters.
Any unverified items are explicitly annotated with # VERIFY_BEFORE_PROD.
"""

from typing import Final, TypedDict

# ==============================================================================
# 1. CPCB NATIONAL AQI SPECIFICATION
# Citation: Central Pollution Control Board (CPCB), Ministry of Environment,
# Forest and Climate Change, Govt. of India (2014 Report "National Air Quality Index")
# Breakpoints: PM2.5 (µg/m³), PM10 (µg/m³), NO2 (µg/m³), O3 (µg/m³),
# CO (mg/m³), SO2 (µg/m³), NH3 (µg/m³)
# Formula: Ip = ((I_Hi - I_Lo) / (BP_Hi - BP_Lo)) * (Cp - BP_Lo) + I_Lo
# Minimum valid pollutant rule: >= 3 pollutants, at least one must be PM2.5 or PM10.
# https://airquality.cpcb.gov.in/ccr_docs/About_AQI.pdf
# VERIFY_BEFORE_PROD: published Severe ranges are open-ended (e.g. PM2.5 250+).
# Retained finite upper endpoints below are legacy interpolation assumptions,
# not newly verified CPCB upper concentration limits. UI labels breakpoint estimates.
# ==============================================================================


class BreakpointRange(TypedDict):
    aqi_low: int
    aqi_high: int
    c_low: float
    c_high: float


CPCB_AQI_CATEGORIES: Final[list[tuple[int, int, str, str]]] = [
    (0, 50, "Good", "#00B050"),
    (51, 100, "Satisfactory", "#92D050"),
    (101, 200, "Moderate", "#FFFF00"),
    (201, 300, "Poor", "#FF9900"),
    (301, 400, "Very Poor", "#FF0000"),
    (401, 500, "Severe", "#C00000"),
]

# Official CPCB Breakpoints Table (24-hr averages for PM2.5, PM10, NO2, SO2, NH3; 8-hr for CO, O3)
# Note: CO concentration is in mg/m³, while others are in µg/m³.
CPCB_BREAKPOINTS: Final[dict[str, list[BreakpointRange]]] = {
    "PM2.5": [
        {"aqi_low": 0, "aqi_high": 50, "c_low": 0.0, "c_high": 30.0},
        {"aqi_low": 51, "aqi_high": 100, "c_low": 31.0, "c_high": 60.0},
        {"aqi_low": 101, "aqi_high": 200, "c_low": 61.0, "c_high": 90.0},
        {"aqi_low": 201, "aqi_high": 300, "c_low": 91.0, "c_high": 120.0},
        {"aqi_low": 301, "aqi_high": 400, "c_low": 121.0, "c_high": 250.0},
        {"aqi_low": 401, "aqi_high": 500, "c_low": 250.1, "c_high": 500.0},
    ],
    "PM10": [
        {"aqi_low": 0, "aqi_high": 50, "c_low": 0.0, "c_high": 50.0},
        {"aqi_low": 51, "aqi_high": 100, "c_low": 51.0, "c_high": 100.0},
        {"aqi_low": 101, "aqi_high": 200, "c_low": 101.0, "c_high": 250.0},
        {"aqi_low": 201, "aqi_high": 300, "c_low": 251.0, "c_high": 350.0},
        {"aqi_low": 301, "aqi_high": 400, "c_low": 351.0, "c_high": 430.0},
        {"aqi_low": 401, "aqi_high": 500, "c_low": 430.1, "c_high": 600.0},
    ],
    "NO2": [
        {"aqi_low": 0, "aqi_high": 50, "c_low": 0.0, "c_high": 40.0},
        {"aqi_low": 51, "aqi_high": 100, "c_low": 41.0, "c_high": 80.0},
        {"aqi_low": 101, "aqi_high": 200, "c_low": 81.0, "c_high": 180.0},
        {"aqi_low": 201, "aqi_high": 300, "c_low": 181.0, "c_high": 280.0},
        {"aqi_low": 301, "aqi_high": 400, "c_low": 281.0, "c_high": 400.0},
        {"aqi_low": 401, "aqi_high": 500, "c_low": 400.1, "c_high": 600.0},
    ],
    "O3": [
        {"aqi_low": 0, "aqi_high": 50, "c_low": 0.0, "c_high": 50.0},
        {"aqi_low": 51, "aqi_high": 100, "c_low": 51.0, "c_high": 100.0},
        {"aqi_low": 101, "aqi_high": 200, "c_low": 101.0, "c_high": 168.0},
        {"aqi_low": 201, "aqi_high": 300, "c_low": 169.0, "c_high": 208.0},
        {"aqi_low": 301, "aqi_high": 400, "c_low": 209.0, "c_high": 748.0},
        {"aqi_low": 401, "aqi_high": 500, "c_low": 748.1, "c_high": 1000.0},
    ],
    "CO": [  # Note: CO is in mg/m³
        {"aqi_low": 0, "aqi_high": 50, "c_low": 0.0, "c_high": 1.0},
        {"aqi_low": 51, "aqi_high": 100, "c_low": 1.1, "c_high": 2.0},
        {"aqi_low": 101, "aqi_high": 200, "c_low": 2.1, "c_high": 10.0},
        {"aqi_low": 201, "aqi_high": 300, "c_low": 10.1, "c_high": 17.0},
        {"aqi_low": 301, "aqi_high": 400, "c_low": 17.1, "c_high": 34.0},
        {"aqi_low": 401, "aqi_high": 500, "c_low": 34.1, "c_high": 60.0},
    ],
    "SO2": [
        {"aqi_low": 0, "aqi_high": 50, "c_low": 0.0, "c_high": 40.0},
        {"aqi_low": 51, "aqi_high": 100, "c_low": 41.0, "c_high": 80.0},
        {"aqi_low": 101, "aqi_high": 200, "c_low": 81.0, "c_high": 380.0},
        {"aqi_low": 201, "aqi_high": 300, "c_low": 381.0, "c_high": 800.0},
        {"aqi_low": 301, "aqi_high": 400, "c_low": 801.0, "c_high": 1600.0},
        {"aqi_low": 401, "aqi_high": 500, "c_low": 1600.1, "c_high": 2000.0},
    ],
    "NH3": [
        {"aqi_low": 0, "aqi_high": 50, "c_low": 0.0, "c_high": 200.0},
        {"aqi_low": 51, "aqi_high": 100, "c_low": 201.0, "c_high": 400.0},
        {"aqi_low": 101, "aqi_high": 200, "c_low": 401.0, "c_high": 800.0},
        {"aqi_low": 201, "aqi_high": 300, "c_low": 801.0, "c_high": 1200.0},
        {"aqi_low": 301, "aqi_high": 400, "c_low": 1201.0, "c_high": 1800.0},
        {"aqi_low": 401, "aqi_high": 500, "c_low": 1800.1, "c_high": 2400.0},
    ],
}

MIN_VALID_POLLUTANTS_COUNT: Final[int] = 3
PM_POLLUTANTS: Final[frozenset[str]] = frozenset({"PM2.5", "PM10"})

# Provider cache policy and WAQI inverse breakpoints
AIR_QUALITY_CACHE_TTL_SECONDS: Final[int] = 1800

# WAQI publishes the 2012 US-EPA PM2.5 scale, distinct from today's EPA scale.
# https://aqicn.org/faq/2013-09-09/revised-pm25-aqi-breakpoints/
# PM10: https://www.airnow.gov/sites/default/files/2020-05/aqi-technical-assistance-document-sept2018.pdf
# VERIFY_BEFORE_PROD: WAQI does not expose a scale version in responses. Confirm
# deployed feeds still use the published scale before treating inversion as precise.
WAQI_PM_BREAKPOINTS: Final[dict[str, list[tuple[int, int, float, float]]]] = {
    "PM2.5": [
        (0, 50, 0, 12),
        (51, 100, 12.1, 35.4),
        (101, 150, 35.5, 55.4),
        (151, 200, 55.5, 150.4),
        (201, 300, 150.5, 250.4),
        (301, 400, 250.5, 350.4),
        (401, 500, 350.5, 500.4),
    ],
    "PM10": [
        (0, 50, 0, 54),
        (51, 100, 55, 154),
        (101, 150, 155, 254),
        (151, 200, 255, 354),
        (201, 300, 355, 424),
        (301, 400, 425, 504),
        (401, 500, 505, 604),
    ],
}

# Physical bounds for sensor data validation (reject absurd/negative readings)
SENSOR_BOUNDS: Final[dict[str, tuple[float, float]]] = {
    "PM2.5": (0.0, 2000.0),  # µg/m³
    "PM10": (0.0, 3000.0),  # µg/m³
    "NO2": (0.0, 1000.0),  # µg/m³
    "O3": (0.0, 1500.0),  # µg/m³
    "CO": (0.0, 100.0),  # mg/m³
    "SO2": (0.0, 2500.0),  # µg/m³
    "NH3": (0.0, 3000.0),  # µg/m³
}

# ==============================================================================
# 4. PHYSIOLOGICAL & EMISSION CONSTANTS
# Citations:
# - Breathing rates: US EPA Exposure Factors Handbook (2011), Chapter 6, Table 6-1.
# - Infiltration factors: Chen & Zhao (2011), Indoor Air; LBNL building studies.
# - Commute exposure multipliers: Goel et al. (2015), Atmospheric Environment.
# - CO2 emission factors: ARAI / CPCB India / Central Electricity Authority (CEA).
# VERIFY_BEFORE_PROD: these scenario values are illustrative, not independently
# calibrated for the user's household/vehicle. UI explicitly labels the assumptions.
# ==============================================================================

# Breathing rate in m³/hour by age group and activity intensity
BREATHING_RATES_M3_PER_HR: Final[dict[str, dict[str, float]]] = {
    "adult": {
        "resting": 0.45,  # Sleeping / reclined
        "sedentary": 0.60,  # Office / seated desk work
        "light": 0.80,  # Slow walking / casual chores
        "moderate": 1.20,  # Brisk walking / normal errand
        "heavy": 2.10,  # Vigorous cycling / running
    },
    "child": {
        "resting": 0.30,
        "sedentary": 0.45,
        "light": 0.60,
        "moderate": 0.80,
        "heavy": 1.40,
    },
    "senior": {
        "resting": 0.40,
        "sedentary": 0.55,
        "light": 0.70,
        "moderate": 1.00,
        "heavy": 1.60,
    },
}

# Indoor PM2.5 Infiltration Factor (fraction of outdoor PM2.5 penetrating indoors without purifier)
INDOOR_INFILTRATION_FACTORS: Final[dict[str, float]] = {
    "sealed_ac": 0.25,  # Tight windows, AC on, good weatherstripping
    "closed_windows": 0.55,  # Standard Indian apartment, closed windows, natural leakage
    "open_windows": 0.90,  # Balcony / windows open for ventilation
}

# Commute Mode Personal PM2.5 Exposure Multiplier relative to ambient roadside station
COMMUTE_EXPOSURE_FACTORS: Final[dict[str, float]] = {
    "electric_2w": 1.0,  # Illustrative open-road scenario
    "petrol_2w": 1.0,  # Illustrative open-road scenario
    "metro": 0.25,  # Underground / elevated AC trains with filtered air
    "petrol_car_solo": 0.20,  # Private car, closed windows, AC recirculation on
    "bus_public": 1.20,  # Regular DTC/BEST bus with open windows
    "auto_rickshaw": 1.50,  # Open 3-wheeler in direct traffic exhaust
    "walking": 1.35,  # Pedestrian on roadside pavement
    "cycling": 1.45,  # Active cycling on roadway (elevated breathing + exhaust)
}

# Commute Mode Tailpipe / Lifecycle CO2 Emissions (grams CO2 per passenger-kilometer)
COMMUTE_CO2_GRAMS_PER_KM: Final[dict[str, float]] = {
    "walking": 0.0,
    "cycling": 0.0,
    "metro": 22.0,  # Indian grid electricity emissions per passenger-km
    "electric_2w": 26.0,  # Grid-charged scooter
    "bus_public": 35.0,  # Public CNG / diesel high-capacity transit
    "petrol_2w": 48.0,  # Standard 110-150cc commuter motorcycle/scooter
    "auto_rickshaw": 72.0,  # CNG auto (average occupancy 1.5)
    "petrol_car_solo": 160.0,  # Solo driver hatchback/sedan
}

# ==============================================================================
# 5. REFERENCE THRESHOLDS & HONESTY LABELS
# Citations:
# - WHO Air Quality Guidelines (2021): 24-hr PM2.5 = 15 µg/m³, Annual = 5 µg/m³
# - India NAAQS (2009): 24-hr PM2.5 = 60 µg/m³, Annual = 40 µg/m³; PM10 24-hr = 100 µg/m³
# - Berkeley Earth Cigarette Equivalence: Muller & Muller (2015)
#   Benchmark: 22 µg/m³ PM2.5 over 24h ~= 1 cigarette
#   Inhaled dose equivalent: 22 µg/m³ * 24h * 0.75 m³/h ~= 396 µg inhaled PM2.5
# ==============================================================================
WHO_2021_PM25_24HR_GUIDELINE: Final[float] = 15.0  # µg/m³
INDIA_NAAQS_PM25_24HR_LIMIT: Final[float] = 60.0  # µg/m³
INDIA_NAAQS_PM10_24HR_LIMIT: Final[float] = 100.0  # µg/m³

# Berkeley Earth benchmark (22 µg/m³ over 24 hours ~= 1 cigarette)
BERKELEY_EARTH_PM25_24HR_BENCHMARK: Final[float] = 22.0  # µg/m³
BERKELEY_EARTH_INHALED_UG_PER_CIGARETTE: Final[float] = 396.0  # µg inhaled mass

# Mandatory Honesty Disclaimers (verbatim compliance with AGENTS.md §5.4)
DISCLAIMER_CIGARETTE_HEURISTIC: Final[str] = (
    "The cigarette equivalent metric is based on the Berkeley Earth benchmark "
    "(~22 µg/m³ over 24 hours ≈ 1 cigarette). This is a public communication heuristic "
    "to contextualize particulate exposure, NOT a clinical diagnosis or medical equivalence."
)

DISCLAIMER_EXPOSURE_BASELINES: Final[str] = (
    "WHO 2021 (15 µg/m³) and India NAAQS (60 µg/m³) 24-hour PM2.5 levels are regulatory "
    "and scientific reference values, not a personal 'safe pollution budget'."
)

DISCLAIMER_SMOG_EPISODE: Final[str] = (
    "Smog Episode Mode is active due to Very Poor / Severe air quality. Sensitive individuals "
    "(children, elderly, asthmatics) should strictly avoid outdoor exertion. If outdoor travel "
    "is unavoidable, wear a properly fitted N95/FFP2 respirator mask (cloth and surgical masks "
    "do not block PM2.5). Consult a doctor or healthcare professional for individualized medical advice."
)

DISCLAIMER_INDOOR_PLANTS: Final[str] = (
    "Indoor plants (such as Areca Palm, Snake Plant, Peace Lily) provide psychological benefits "
    "and marginal VOC absorption under static laboratory conditions. For real-world PM2.5 particulate "
    "reduction, mechanical HEPA air purifiers, gap sealing, and timed ventilation are the primary effective measures."
)

# ==============================================================================
# 6. GROK (xAI) API & MODEL CONFIGURATION
# Citation: xAI API Documentation (https://docs.x.ai)
# Model identifier read strictly from environment variable; default fallback provided.
# ==============================================================================
GROK_DEFAULT_BASE_URL: Final[str] = "https://api.x.ai/v1"
GROQ_BASE_URL: Final[str] = "https://api.groq.com/openai/v1"
GROK_TIMEOUT_SECONDS: Final[float] = 15.0

# ==============================================================================
# 7. OPEN-METEO AIR QUALITY (Phase 6 Optional)
# Citation: Open-Meteo Air Quality API (https://open-meteo.com/en/docs/air-quality-api)
# Note: Modelled data must be explicitly labeled and structurally isolated from live sensor data.
# ==============================================================================
OPEN_METEO_BASE_URL: Final[str] = "https://air-quality-api.open-meteo.com/v1/air-quality"
