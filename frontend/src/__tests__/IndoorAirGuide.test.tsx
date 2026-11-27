import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "jest-axe";
import { IndoorAirGuide } from "../IndoorAirGuide";
import type { RoomCADRResult } from "../api/types";

const MOCK_CADR: RoomCADRResult = {
  dimensions: { length_m: 5, width_m: 4, height_m: 2.8 },
  factors: {
    has_kitchen_chimney: true,
    burns_incense_agarbatti: false,
    has_unsealed_balcony: false,
  },
  source_multiplier: 1,
  room_volume_m3: 56.0,
  target_ach: 5.0,
  required_cadr_m3_per_hr: 280.0,
  required_cadr_cfm: 164.8,
  sealing_and_source_guidance:
    "Door sweep and silicone weatherstripping required under entrance.",
  ventilation_recommendation:
    "Ventilate only during lowest smog window (1:00 PM – 3:30 PM).",
  plants_footnote:
    "NASA-cited plants achieve <1% PM2.5 removal in real homes and do NOT replace HEPA purifiers.",
};

describe("IndoorAirGuide Component", () => {
  it("renders CADR sizing metrics in m³/h and CFM", () => {
    render(<IndoorAirGuide initialGuidance={MOCK_CADR} />);

    expect(screen.getByText(/Required Air Purifier CADR/i)).toBeInTheDocument();
    expect(screen.getByText(/280/)).toBeInTheDocument();
    expect(screen.getByText(/CFM/i)).toBeInTheDocument();
    expect(screen.getByLabelText("Target ACH")).toHaveValue("5");
  });

  it("keeps applied room volume visible until an edited dimension succeeds", async () => {
    const user = userEvent.setup();
    const onRecalc = vi.fn();

    render(
      <IndoorAirGuide
        initialGuidance={MOCK_CADR}
        initialDimensions={{ length_m: 5.0, width_m: 4.0, height_m: 2.8 }}
        onRecalculate={onRecalc}
      />,
    );

    const lengthInput = screen.getByLabelText(/Length \(m\)/i);
    await user.clear(lengthInput);
    await user.type(lengthInput, "6.0");
    await user.click(screen.getByRole("button", { name: /Show the Math/i }));
    expect(
      screen.getByText(/Volume \(m³\) = Length \(5m\).*56 m³/),
    ).toBeInTheDocument();
    expect(screen.queryByText(/Clinical requirement/i)).not.toBeInTheDocument();

    // Form submit triggers callback
    const submitBtn = screen.getByRole("button", {
      name: /Update CADR & Sealing Advisory/i,
    });
    await user.click(submitBtn);

    expect(onRecalc).toHaveBeenCalledWith(
      { length_m: 6, width_m: 4, height_m: 2.8 },
      expect.objectContaining({ has_unsealed_balcony: false }),
      5,
    );
  });

  it("renders the mandatory scientific footnote on NASA air-purifying plants", () => {
    render(<IndoorAirGuide initialGuidance={MOCK_CADR} />);

    expect(
      screen.getByText(/Scientific Footnote on NASA Air-Purifying Plants/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/do NOT replace HEPA purifiers/i),
    ).toBeInTheDocument();
  });

  it("expands the Show the Math drawer with CADR formulas and ACH benchmarks", async () => {
    const user = userEvent.setup();

    render(<IndoorAirGuide initialGuidance={MOCK_CADR} />);

    const mathBtn = screen.getByRole("button", { name: /Show the Math/i });
    expect(
      screen.queryByText(/Deterministic CADR Formula/i),
    ).not.toBeInTheDocument();

    await user.click(mathBtn);

    expect(screen.getByText(/Deterministic CADR Formula/i)).toBeInTheDocument();
    expect(screen.getByText(/Target ACH Benchmarks/i)).toBeInTheDocument();
  });

  it("has zero accessibility violations via jest-axe", async () => {
    const { container } = render(
      <IndoorAirGuide initialGuidance={MOCK_CADR} />,
    );

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
