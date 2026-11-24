import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "jest-axe";
import { describe, expect, it } from "vitest";
import { RecommendationCards } from "../common/RecommendationCards";
import type { RecommendationCard } from "../api/types";
import { DELHI_PLAN_FIXTURE } from "../test/fixtures/dailyPlan";

const card: RecommendationCard = {
  id: "conversion",
  pillar: "routine",
  title: "Estimated commute impact",
  why: "Lower roadside exposure depends on travel mode and breathing rate.",
  quantified_impact:
    "Estimated inhaled particulate dose uses the configured factors.",
  station_metadata: {
    ...DELHI_PLAN_FIXTURE.station_metadata,
    status: "modelled_live",
    source: "Open-Meteo CAMS (Modelled)",
  },
  data_confidence: "Low",
  confidence_reason: "Model output, not measured station data.",
  math_breakdown: {
    formula_name: "Dose",
    formula_expression: "Dose = concentration × breathing rate × hours",
    inputs: {
      pollutant_conversion: "WAQI inverse US-EPA reconstruction",
      concentration: 55.4,
    },
    output_value: "5 µg",
    reference_benchmark: "Not a personal safe budget",
    scientific_citation: "Illustrative exposure scenario",
  },
};

describe("Recommendation transparency", () => {
  it("shows modelled provenance and exposes actual conversion inputs on expansion", async () => {
    const user = userEvent.setup();
    const { container } = render(<RecommendationCards cards={[card]} />);
    expect(screen.getByText(/Modelled current estimate/)).toBeInTheDocument();
    expect(screen.getByText(/Data Confidence: Low/)).toBeInTheDocument();
    expect(screen.queryByText(/WAQI inverse/)).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /Show the Math/ }));
    expect(screen.getByText(/WAQI inverse/)).toBeInTheDocument();
    expect(screen.getByText("55.4")).toBeInTheDocument();
    expect(await axe(container)).toHaveNoViolations();
  });
});
