import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "jest-axe";
import { LandingView } from "../components/LandingView";

describe("LandingView Component", () => {
  it("renders the Urbero display title, subtitle, and Get Started CTA", () => {
    const handleStart = vi.fn();
    render(<LandingView onGetStarted={handleStart} />);

    expect(screen.getByText("Urbero")).toBeInTheDocument();
    expect(
      screen.getByText(/Deterministic Urban Air Quality & Household Exposure Assistant/i)
    ).toBeInTheDocument();

    const startBtn = screen.getByRole("button", { name: /Get Started/i });
    expect(startBtn).toBeInTheDocument();
  });

  it("calls onGetStarted when Get Started button is clicked", async () => {
    const user = userEvent.setup();
    const handleStart = vi.fn();
    render(<LandingView onGetStarted={handleStart} />);

    const startBtn = screen.getByRole("button", { name: /Get Started/i });
    await user.click(startBtn);

    expect(handleStart).toHaveBeenCalledTimes(1);
  });

  it("has zero accessibility violations via jest-axe", async () => {
    const { container } = render(<LandingView onGetStarted={vi.fn()} />);

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
