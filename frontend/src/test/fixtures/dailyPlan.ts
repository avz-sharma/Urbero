import type { DailyPlanResponse } from "../../api/types";

/**
 * Synthetic UI test fixture. Never imported by production code.
 * Derived strictly from single-source-of-truth OpenAPI schema types.
 */
export const DELHI_PLAN_FIXTURE: DailyPlanResponse = {
  history_source: "Open-Meteo CAMS (Modelled) — test fixture",
  timestamp: new Date().toISOString(),
  city: "Delhi",
  station_metadata: {
    source: "WAQI / CPCB",
    conversion_note: "WAQI inverse PM reconstruction; estimate only.",
    station: "Anand Vihar, Delhi - DPCC",
    distance_km: 3.8,
    observed_at: new Date().toISOString(),
    fetched_at: new Date().toISOString(),
    status: "live",
    is_reference_grade: true,
  },
  aqi_result: {
    overall_aqi: 345,
    dominant_pollutant: "PM2.5",
    category: "Very Poor",
    color_code: "#E53E3E",
    sub_indices: [
      {
        pollutant: "PM2.5",
        concentration: 165.0,
        unit: "µg/m³",
        sub_index: 345,
        category: "Very Poor",
        color_code: "#E53E3E",
      },
      {
        pollutant: "PM10",
        concentration: 285.0,
        unit: "µg/m³",
        sub_index: 245,
        category: "Poor",
        color_code: "#DD6B20",
      },
      {
        pollutant: "NO2",
        concentration: 92.0,
        unit: "µg/m³",
        sub_index: 115,
        category: "Moderate",
        color_code: "#D69E2E",
      },
    ],
    is_valid: true,
    validation_message:
      "Valid CPCB AQI based on 3 pollutants including particulate parameters.",
  },
  data_confidence: {
    level: "High",
    score_percent: 92,
    reason:
      "Station within 3.8 km, observed 14 mins ago, reference-grade sensor reporting 3 valid parameters.",
  },
  smog_episode_active: true,
  medical_disclaimer:
    "Smog Episode Mode is active due to Very Poor / Severe air quality. Sensitive individuals (children, elderly, asthmatics) should strictly avoid outdoor exertion. If outdoor travel is unavoidable, wear a properly fitted N95/FFP2 respirator mask (cloth and surgical masks do not block PM2.5). Consult a doctor or healthcare professional for individualized medical advice.",
  routine_optimization: {
    activities: [
      {
        activity_id: "walk_1",
        activity_name: "Dada Ji Morning Walk",
        member_name: "Dada Ji (Asthmatic)",
        original_start_hour: 6.5,
        original_end_hour: 7.5,
        optimized_start_hour: 14.0,
        optimized_end_hour: 15.0,
        is_shifted: true,
        is_shifted_indoors: true,
        baseline_inhaled_pm25_ug: 42.0,
        optimized_inhaled_pm25_ug: 12.5,
        dose_reduction_ug: 29.5,
        recommendation_note:
          "Shift walk indoors to HEPA-purified living room; outdoor thermal inversion peaks at 6:30 AM.",
      },
      {
        activity_id: "kid_play",
        activity_name: "Aarav Outdoor Sports",
        member_name: "Aarav (8yo)",
        original_start_hour: 17.0,
        original_end_hour: 18.5,
        optimized_start_hour: 13.5,
        optimized_end_hour: 14.5,
        is_shifted: true,
        is_shifted_indoors: false,
        baseline_inhaled_pm25_ug: 38.5,
        optimized_inhaled_pm25_ug: 14.0,
        dose_reduction_ug: 24.5,
        recommendation_note:
          "Move sports to early afternoon solar dispersion window; evening cooling traps surface particulates.",
      },
    ],
    total_baseline_dose_ug: 80.5,
    total_optimized_dose_ug: 26.5,
    total_dose_reduction_ug: 54.0,
    total_dose_reduction_percent: 67.1,
    smog_episode_active: true,
    smog_episode_advisory:
      "Fitted N95/FFP2 respirator mandatory if outdoors. Cloth masks offer zero PM2.5 seal.",
    clean_air_day: false,
    overall_advisory:
      "Severe winter smog episode in effect. Realign outdoor activities to the 1:00 PM – 3:30 PM solar heating window.",
  },
  commute_comparisons: [
    {
      mode: "metro",
      label: "Delhi Metro (Blue Line)",
      distance_km: 18.0,
      duration_minutes: 42,
      tailpipe_co2_grams: 320,
      personal_inhaled_pm25_ug: 22.4,
      exposure_multiplier: 0.25,
      planet_vs_lungs_note:
        "Optimal win-win: 85% lower tailpipe CO2 vs solo car and enclosed station/train air filtration reduces PM2.5 dose by 78%.",
    },
    {
      mode: "cycling",
      label: "Bicycle (Arterial Highway)",
      distance_km: 18.0,
      duration_minutes: 65,
      tailpipe_co2_grams: 0,
      personal_inhaled_pm25_ug: 185.0,
      exposure_multiplier: 2.0,
      planet_vs_lungs_note:
        "Planet vs Lungs Hazard: 0g tailpipe CO2, but high ventilation rate (2.8 m³/h) next to traffic yields 8x higher PM2.5 dose during smog.",
    },
    {
      mode: "petrol_car_solo",
      label: "Petrol Car (Solo, AC Recirculating)",
      distance_km: 18.0,
      duration_minutes: 48,
      tailpipe_co2_grams: 2880,
      personal_inhaled_pm25_ug: 19.5,
      exposure_multiplier: 0.2,
      planet_vs_lungs_note:
        "Lungs protected by vehicle cabin filtration, but emits 2.88 kg tailpipe CO2.",
    },
  ],
  errand_merger: {
    ordered_stops: [
      {
        id: "s1",
        name: "Neighborhood Pharmacy",
        category: "pharmacy",
        duration_minutes: 15,
        distance_from_home_km: 1.2,
        window_open_hour: 10.0,
        window_close_hour: 20.0,
      },
      {
        id: "s2",
        name: "Organic Grocery Store",
        category: "groceries",
        duration_minutes: 25,
        distance_from_home_km: 2.5,
        window_open_hour: 11.0,
        window_close_hour: 19.0,
      },
      {
        id: "s3",
        name: "School Dismissal Pickup",
        category: "school",
        duration_minutes: 20,
        distance_from_home_km: 3.1,
        window_open_hour: 13.5,
        window_close_hour: 15.0,
      },
    ],
    recommended_start_hour: 13.0,
    recommended_end_hour: 15.5,
    baseline_separate_distance_km: 14.8,
    merged_loop_distance_km: 8.4,
    distance_saved_km: 6.4,
    travel_mode: "auto_rickshaw",
    emissions_factor_g_per_km: 160,
    tailpipe_co2_saved_grams: 1024,
    baseline_inhaled_pm25_ug: 48.2,
    optimized_inhaled_pm25_ug: 17.0,
    pm25_dose_reduction_percent: 64.7,
    rationale: "Merged 3 errands into single loop during afternoon dispersion.",
  },
  room_cadr_guidance: {
    dimensions: { length_m: 5, width_m: 4, height_m: 2.8 },
    factors: {
      has_kitchen_chimney: true,
      burns_incense_agarbatti: false,
      has_unsealed_balcony: false,
    },
    source_multiplier: 1,
    room_volume_m3: 56,
    target_ach: 5.0,
    required_cadr_m3_per_hr: 280,
    required_cadr_cfm: 164.8,
    sealing_and_source_guidance:
      "Door sweep and silicone foam weatherstripping required under main entrance to cut particulate infiltration by 42%.",
    ventilation_recommendation:
      "Ventilate only during lowest smog window (1:00 PM – 3:30 PM). Keep sealed tightly during morning and evening inversions.",
    plants_footnote:
      "The 1989 NASA Clean Air Study was conducted in sealed chambers. Potted plants (Areca Palm, Snake Plant) achieve <1% PM2.5 removal in real homes and do NOT replace HEPA purifiers.",
  },
  recommendation_cards: [],
  exposure_reference_labels: {
    cigarette_heuristic:
      "The Berkeley Earth benchmark is a public communication heuristic to contextualize particulate exposure, not a clinical diagnosis or medical equivalence.",
    reference_values:
      "WHO 2021 (15 µg/m³) and India NAAQS (60 µg/m³) 24-hour PM2.5 levels are regulatory and scientific reference values, not a personal 'safe pollution budget'.",
  },
  whatsapp_card: {
    headline: "🌅 Urbero Family Air Advisory — South Delhi (Anand Vihar)",
    language: "english",
    current_aqi_badge: "345 (Very Poor)",
    key_actions: [
      "Shift Dada Ji's morning walk from 6:30 AM to 2:00 PM indoors.",
      "Keep living room air purifier on High (CADR 320 m³/h).",
      "Rahul should commute via Blue Line Metro instead of driving solo.",
    ],
    commute_tip:
      "Take Blue Line Metro; avoid cycling during morning inversion.",
    indoor_tip: "Run purifier at 324 m³/h; seal main balcony door gaps.",
    sensitive_member_alert:
      "Asthmatics and 8yo child must wear fitted N95/FFP2 masks outdoors.",
    formatted_message: `🌅 Urbero Family Air Advisory — South Delhi (Anand Vihar)

📊 Air Status: AQI 345 | Very Poor (Anand Vihar, Delhi - DPCC)
🛡️ Data Confidence: High (Station within 3.8 km, observed 14 mins ago)

• Asthmatics and 8yo child must wear fitted N95/FFP2 masks outdoors.
• Take Blue Line Metro; avoid cycling during morning inversion.
• Run purifier at 324 m³/h; seal main balcony door gaps.

💡 Impact: Schedule shift cuts family PM2.5 dose by 54 µg (67.1%).
⚠️ Note: The Berkeley Earth cigarette equivalence (~22 µg/m³ for 24h = 1 cigarette) is a communication heuristic, not a medical diagnosis.`,
  },
  community_brief: {
    rwa_society_advisory:
      "Run clubhouse purifiers on high; seal common area entry doors.",
    school_outdoor_activity_recommendation:
      "Cancel morning outdoor physical exercise and school assemblies before 11:00 AM.",
    mask_and_health_guidance:
      "Fitted N95/FFP2 masks recommended for outdoor transit.",
    formatted_brief: `🏛️ *RWA & School Smog Advisory — South Delhi*
• Current AQI: 345 (Very Poor, Anand Vihar CPCB station).
• Action for Schools: Suspend morning outdoor assemblies and sports before 11:00 AM.
• Action for RWAs: Ensure common clubrooms run HEPA air filtration. Advise residents to seal gap leaks.
• Medical Advisory: Asthmatics and seniors should keep rescue inhalers accessible and consult their doctor.`,
  },
};
