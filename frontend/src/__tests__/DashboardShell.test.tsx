import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "jest-axe";
import { DashboardShell } from "../components/DashboardShell";
import { INDIAN_PRESETS } from "../HouseholdProfile";
import { DELHI_PLAN_FIXTURE } from "../test/fixtures/dailyPlan";

describe("DashboardShell Component", () => {
  const defaultProps = {
    planData: DELHI_PLAN_FIXTURE,
    selectedPreset: INDIAN_PRESETS[0],
    onSelectPreset: vi.fn(),
    activeLocation: {
      label: "South Delhi, Delhi",
      lat: 28.6139,
      lon: 77.209,
      origin: "preset" as const,
    },
    onSelectLocation: vi.fn(),
    cadrGuidance: DELHI_PLAN_FIXTURE.room_cadr_guidance,
    onRecalculateCADR: vi.fn(),
  };

  it("renders all 4 tabs in the horizontal tab bar", () => {
    render(<DashboardShell {...defaultProps} />);

    expect(
      screen.getByRole("tablist", { name: /Urbero Workspace Sections/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Overview/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Routine/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Indoor/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Briefings/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Overview/i })).toHaveAttribute("id", "tab-overview");
    expect(screen.getByRole("tab", { name: /Routine/i })).toHaveAttribute("id", "tab-routine");
    expect(screen.getByRole("tab", { name: /Indoor/i })).toHaveAttribute("id", "tab-indoor");
    expect(screen.getByRole("tab", { name: /Briefings/i })).toHaveAttribute("id", "tab-briefings");
  });

  it("moves keyboard focus and selection together with arrows and End", async () => {
    const user = userEvent.setup();
    render(<DashboardShell {...defaultProps} selectedPreset={null} />);
    const overview = screen.getByRole("tab", { name: /Overview/i });
    overview.focus();
    await user.keyboard("{ArrowRight}");
    expect(screen.getByRole("tab", { name: /Routine/i })).toHaveFocus();
    await user.keyboard("{End}");
    const briefings = screen.getByRole("tab", { name: /Briefings/i });
    expect(briefings).toHaveFocus();
    expect(briefings).toHaveAttribute("aria-selected", "true");
  });

  it("switches to Routine & Commute tab on click without rendering briefings", async () => {
    const user = userEvent.setup();
    render(<DashboardShell {...defaultProps} />);

    const routineTab = screen.getByRole("tab", { name: /Routine/i });
    await user.click(routineTab);

    expect(routineTab).toHaveAttribute("aria-selected", "true");
    expect(
      screen.getByText(/Diurnal Household Schedule Optimization/i),
    ).toBeInTheDocument();
    // Briefings card should NOT be in Routine & Commute tab
    expect(screen.queryByText(/WhatsApp Family Card/i)).not.toBeInTheDocument();
  });

  it("switches to Indoor Air & CADR tab on click", async () => {
    const user = userEvent.setup();
    render(<DashboardShell {...defaultProps} />);

    const indoorTab = screen.getByRole("tab", { name: /Indoor/i });
    await user.click(indoorTab);

    expect(indoorTab).toHaveAttribute("aria-selected", "true");
    expect(
      screen.getByText(/3\. Indoor Air Quality & CADR Action Engine/i),
    ).toBeInTheDocument();
  });

  it("switches to Briefings & Impact tab on click", async () => {
    const user = userEvent.setup();
    render(<DashboardShell {...defaultProps} />);

    const briefingsTab = screen.getByRole("tab", { name: /Briefings/i });
    await user.click(briefingsTab);

    expect(briefingsTab).toHaveAttribute("aria-selected", "true");
    expect(screen.getByText(/WhatsApp Family Card/i)).toBeInTheDocument();
  });

  it("has zero accessibility violations via jest-axe on initial render", async () => {
    const { container } = render(<DashboardShell {...defaultProps} />);

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
