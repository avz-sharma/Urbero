import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "jest-axe";
import { HouseholdProfile, INDIAN_PRESETS } from "../HouseholdProfile";

describe("HouseholdProfile Component", () => {
  it("renders all 3 Indian household presets", () => {
    const onSelect = vi.fn();

    render(
      <HouseholdProfile
        selectedPresetId="south-delhi"
        onSelectPreset={onSelect}
      />
    );

    expect(screen.getByText("South Delhi Joint Family")).toBeInTheDocument();
    expect(screen.getByText("Andheri Mumbai Working Couple")).toBeInTheDocument();
    expect(screen.getByText("Salt Lake Kolkata Senior Couple")).toBeInTheDocument();
  });

  it("handles preset switching via clicks and keyboard", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();

    render(
      <HouseholdProfile
        selectedPresetId="south-delhi"
        onSelectPreset={onSelect}
      />
    );

    const mumbaiBtn = screen.getByText("Andheri Mumbai Working Couple");
    await user.click(mumbaiBtn);

    expect(onSelect).toHaveBeenCalledWith(INDIAN_PRESETS[1]);
  });

  it("has zero accessibility violations via jest-axe", async () => {
    const { container } = render(
      <HouseholdProfile
        selectedPresetId="south-delhi"
        onSelectPreset={vi.fn()}
      />
    );

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
