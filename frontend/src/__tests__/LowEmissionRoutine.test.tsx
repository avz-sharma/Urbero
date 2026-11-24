import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "jest-axe";
import { LowEmissionRoutine } from "../LowEmissionRoutine";
import type {
  CommunityBrief,
  CommuteModeComparison,
  RoutineOptimizationResult,
  WhatsAppFamilyCard,
} from "../api/types";

const MOCK_COMMUTE: CommuteModeComparison[] = [
  {
    mode: "metro",
    label: "Delhi Metro (Blue Line)",
    distance_km: 18.0,
    duration_minutes: 42,
    tailpipe_co2_grams: 320,
    personal_inhaled_pm25_ug: 22.4,
    exposure_multiplier: 0.25,
    planet_vs_lungs_note: "Optimal win-win: 85% lower tailpipe CO2 vs solo car and enclosed station air filtration reduces PM2.5 dose.",
  },
  {
    mode: "cycling",
    label: "Bicycle (Arterial Highway)",
    distance_km: 18.0,
    duration_minutes: 65,
    tailpipe_co2_grams: 0,
    personal_inhaled_pm25_ug: 185.0,
    exposure_multiplier: 2.0,
    planet_vs_lungs_note: "Planet vs Lungs Hazard: 0g tailpipe CO2, but high ventilation rate yields 8x higher PM2.5 dose during smog.",
  },
];

const MOCK_ROUTINE: RoutineOptimizationResult = {
  activities: [
    {
      activity_id: "walk_1",
      activity_name: "Dada Ji Morning Walk",
      member_name: "Dada Ji",
      original_start_hour: 6.5,
      original_end_hour: 7.5,
      optimized_start_hour: 14.0,
      optimized_end_hour: 15.0,
      is_shifted: true,
      is_shifted_indoors: true,
      baseline_inhaled_pm25_ug: 42.0,
      optimized_inhaled_pm25_ug: 12.5,
      dose_reduction_ug: 29.5,
      recommendation_note: "Shift indoors to living room; morning thermal inversion peaks early.",
    },
  ],
  total_baseline_dose_ug: 42.0,
  total_optimized_dose_ug: 12.5,
  total_dose_reduction_ug: 29.5,
  total_dose_reduction_percent: 70.2,
  smog_episode_active: true,
  smog_episode_advisory: "Fitted N95/FFP2 respirator mandatory outdoors. Cloth masks provide 0% seal.",
  clean_air_day: false,
  overall_advisory: "Severe winter smog episode in effect.",
};

const MOCK_WHATSAPP: WhatsAppFamilyCard = {
  headline: "Family Advisory",
  language: "english",
  current_aqi_badge: "345 (Very Poor)",
  key_actions: ["Shift walk indoors"],
  commute_tip: "Take Metro",
  indoor_tip: "Run purifier",
  sensitive_member_alert: "Consult doctor",
  formatted_message: "🌅 Family Advisory: AQI 345. Take Metro. Seal windows.",
};

const MOCK_COMMUNITY: CommunityBrief = {
  rwa_society_advisory: "Run clubhouse purifiers",
  school_outdoor_activity_recommendation: "Cancel morning outdoor recess",
  mask_and_health_guidance: "Fitted N95 masks for outdoor transit",
  formatted_brief: "🏛️ Community Advisory: High AQI. Cancel outdoor sports.",
};

describe("LowEmissionRoutine Component", () => {
  it("renders Smog Episode Alert with fitted N95 and doctor lines when active", () => {
    render(
      <LowEmissionRoutine
        commuteOptions={MOCK_COMMUTE}
        routineResult={MOCK_ROUTINE}
        whatsappCard={MOCK_WHATSAPP}
        communityBrief={MOCK_COMMUNITY}
        smogEpisodeActive={true}
      />
    );

    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.getByText(/SMOG EPISODE ACTIVE/i)).toBeInTheDocument();
    expect(screen.getByText(/fitted N95\/FFP2 respirator mask/i)).toBeInTheDocument();
    expect(screen.getByText(/cloth and surgical masks provide zero seal/i)).toBeInTheDocument();
    expect(screen.getByText(/Consult a doctor/i)).toBeInTheDocument();
  });

  it("does not render Smog Episode Alert when inactive", () => {
    render(
      <LowEmissionRoutine
        commuteOptions={MOCK_COMMUTE}
        routineResult={{ ...MOCK_ROUTINE, smog_episode_active: false }}
        whatsappCard={MOCK_WHATSAPP}
        communityBrief={MOCK_COMMUNITY}
        smogEpisodeActive={false}
      />
    );

    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("renders Planet vs. Lungs commute mode comparison table", () => {
    render(
      <LowEmissionRoutine
        commuteOptions={MOCK_COMMUTE}
        routineResult={MOCK_ROUTINE}
        whatsappCard={MOCK_WHATSAPP}
        communityBrief={MOCK_COMMUNITY}
        smogEpisodeActive={true}
      />
    );

    expect(screen.getByText("Delhi Metro (Blue Line)")).toBeInTheDocument();
    expect(screen.getByText("Bicycle (Arterial Highway)")).toBeInTheDocument();
    expect(screen.getByText(/Planet vs Lungs Hazard/i)).toBeInTheDocument();
  });

  it("allows switching between WhatsApp and Community Brief tabs and copying", async () => {
    const user = userEvent.setup();

    render(
      <LowEmissionRoutine
        commuteOptions={MOCK_COMMUTE}
        routineResult={MOCK_ROUTINE}
        whatsappCard={MOCK_WHATSAPP}
        communityBrief={MOCK_COMMUNITY}
        smogEpisodeActive={true}
      />
    );

    expect(screen.getByText(/Family Advisory: AQI 345/i)).toBeInTheDocument();

    const commTab = screen.getByRole("button", { name: /RWA & School Brief/i });
    await user.click(commTab);

    expect(screen.getByText(/Community Advisory: High AQI/i)).toBeInTheDocument();

    const copyBtn = screen.getByRole("button", { name: /Copy Community Brief/i });
    await user.click(copyBtn);
    expect(await screen.findByText(/Copied to Clipboard!/i)).toBeInTheDocument();
  });

  it("has zero accessibility violations via jest-axe", async () => {
    const { container } = render(
      <LowEmissionRoutine
        commuteOptions={MOCK_COMMUTE}
        routineResult={MOCK_ROUTINE}
        whatsappCard={MOCK_WHATSAPP}
        communityBrief={MOCK_COMMUNITY}
        smogEpisodeActive={true}
      />
    );

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
