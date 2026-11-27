import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "jest-axe";
import { ImpactJustification } from "../ImpactJustification";
import { DELHI_PLAN_FIXTURE } from "../test/fixtures/dailyPlan";
import type {
  ConfidenceResult,
  CPCBAQIResult,
  MergedErrandsResult,
  StationMetadataSchema,
} from "../api/types";

const MOCK_AQI: CPCBAQIResult = {
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
  ],
  is_valid: true,
  validation_message: "Valid CPCB calculation.",
};

const MOCK_STATION: StationMetadataSchema = {
  source: "WAQI / CPCB",
  conversion_note: "WAQI inverse PM reconstruction; estimate only.",
  station: "Anand Vihar, Delhi - DPCC",
  distance_km: 3.8,
  observed_at: new Date().toISOString(),
  fetched_at: new Date().toISOString(),
  status: "live",
  is_reference_grade: true,
};

const MOCK_CONFIDENCE: ConfidenceResult = {
  level: "High",
  score_percent: 92,
  reason: "Station within 3.8 km, observed recently.",
};

const MOCK_ERRANDS: MergedErrandsResult = {
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
  ],
  recommended_start_hour: 13.0,
  recommended_end_hour: 15.0,
  baseline_separate_distance_km: 12.0,
  merged_loop_distance_km: 6.8,
  distance_saved_km: 5.2,
  travel_mode: "auto_rickshaw",
  emissions_factor_g_per_km: 160,
  tailpipe_co2_saved_grams: 832,
  baseline_inhaled_pm25_ug: 40.0,
  optimized_inhaled_pm25_ug: 15.0,
  pm25_dose_reduction_percent: 62.5,
  rationale: "Cleanest window.",
};

describe("ImpactJustification Component", () => {
  it("renders CPCB AQI card with dominant pollutant, station metadata, and Data Confidence badge", () => {
    render(
      <ImpactJustification
        aqiData={MOCK_AQI}
        stationMetadata={MOCK_STATION}
        dataConfidence={MOCK_CONFIDENCE}
        errandsResult={MOCK_ERRANDS}
      />,
    );

    expect(screen.getAllByText("345").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Very Poor").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Anand Vihar, Delhi - DPCC")).toBeInTheDocument();
    expect(screen.getByText(/Data Confidence: High/i)).toBeInTheDocument();
  });

  it("renders accessible pollutant sub-indices table", () => {
    render(
      <ImpactJustification
        aqiData={MOCK_AQI}
        stationMetadata={MOCK_STATION}
        dataConfidence={MOCK_CONFIDENCE}
        errandsResult={MOCK_ERRANDS}
      />,
    );

    expect(screen.getByText("165 µg/m³")).toBeInTheDocument();
    expect(screen.getByText("285 µg/m³")).toBeInTheDocument();
  });

  it("renders consolidated errand loop metrics", () => {
    render(
      <ImpactJustification
        aqiData={MOCK_AQI}
        stationMetadata={MOCK_STATION}
        dataConfidence={MOCK_CONFIDENCE}
        errandsResult={MOCK_ERRANDS}
      />,
    );

    expect(screen.getByText(/5.2/)).toBeInTheDocument();
    expect(screen.getByText(/832/)).toBeInTheDocument();
    expect(screen.getByText(/62.5%/)).toBeInTheDocument();
    expect(screen.getByText(/Neighborhood Pharmacy/i)).toBeInTheDocument();
  });

  it("expands Show the Math drawer with Berkeley Earth and WHO/NAAQS disclaimers", async () => {
    const user = userEvent.setup();

    render(
      <ImpactJustification
        aqiData={MOCK_AQI}
        stationMetadata={MOCK_STATION}
        dataConfidence={MOCK_CONFIDENCE}
        errandsResult={MOCK_ERRANDS}
        exposureLabels={DELHI_PLAN_FIXTURE.exposure_reference_labels}
      />,
    );

    const mathBtn = screen.getByRole("button", {
      name: /Show the Math: CPCB Linear Breakpoint Formula/i,
    });
    await user.click(mathBtn);

    expect(
      screen.getByText(/Berkeley Earth Cigarette Heuristic/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/public communication heuristic/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/WHO and India NAAQS reference values/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/not a personal 'safe pollution budget'/i),
    ).toBeInTheDocument();
    expect(
      screen.queryByText(/in terms of inhaled mass/i),
    ).not.toBeInTheDocument();
  });

  it("has zero accessibility violations via jest-axe", async () => {
    const { container } = render(
      <ImpactJustification
        aqiData={MOCK_AQI}
        stationMetadata={MOCK_STATION}
        dataConfidence={MOCK_CONFIDENCE}
        errandsResult={MOCK_ERRANDS}
      />,
    );

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
