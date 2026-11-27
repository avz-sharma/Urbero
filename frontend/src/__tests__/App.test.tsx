import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
  render,
  screen,
  act,
  waitFor,
  fireEvent,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "jest-axe";
import App from "../App";
import { DELHI_PLAN_FIXTURE } from "../test/fixtures/dailyPlan";

describe("App Integration & Accessibility", () => {
  it.each(["light", "dark"])(
    "passes automated accessibility checks across the workspace in %s mode",
    async (theme) => {
      localStorage.setItem("urbero-theme", theme);
      const user = userEvent.setup();
      const { container } = render(<App />);
      expect(await axe(container)).toHaveNoViolations();
      await user.click(screen.getByRole("button", { name: /Get Started/i }));
      expect(
        screen.getByRole("heading", { name: /Choose your location/i }),
      ).toHaveFocus();
      expect(await axe(container)).toHaveNoViolations();
      await user.click(screen.getByRole("button", { name: /^Noida$/i }));
      for (const name of [/Overview/i, /Routine/i, /Indoor/i, /Briefings/i]) {
        await user.click(await screen.findByRole("tab", { name }));
        const tab = screen.getByRole("tab", { name });
        const panel = await screen.findByRole("tabpanel", { name });
        expect(panel.id).toBe(tab.getAttribute("aria-controls"));
        expect(await axe(container)).toHaveNoViolations();
      }
      localStorage.removeItem("urbero-theme");
    },
  );
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => DELHI_PLAN_FIXTURE,
      }),
    );
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("starts with no selected area and makes no requests on either landing or location gate", async () => {
    const user = userEvent.setup();
    render(<App />);
    expect(fetch).not.toHaveBeenCalled();
    await user.click(screen.getByRole("button", { name: /Open Workspace/i }));
    expect(
      screen.getByRole("heading", { name: /Choose your location/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Use My Live Location/i }),
    ).toBeInTheDocument();
    expect(screen.queryByRole("tablist")).not.toBeInTheDocument();
    expect(screen.queryByRole("radio")).not.toBeInTheDocument();
    expect(fetch).not.toHaveBeenCalled();
  });

  it("shows provider failure without fabricated recommendations, then retries", async () => {
    const user = userEvent.setup();
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: false,
      status: 503,
    } as Response);
    render(<App initialView="dashboard" />);
    await user.click(screen.getByRole("button", { name: /^Delhi$/i }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      /temporarily unavailable/i,
    );
    expect(screen.queryByRole("tablist")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Retry" }));
    expect(
      await screen.findByRole("tab", { name: /Overview/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("main")).toHaveFocus();
  });

  it("preserves GPS coordinates when applying a household preset", async () => {
    const user = userEvent.setup();
    const coordinates = { latitude: 19.1363, longitude: 72.8277 };
    Object.defineProperty(navigator, "geolocation", {
      configurable: true,
      value: {
        getCurrentPosition: (success: PositionCallback) =>
          success({ coords: coordinates } as GeolocationPosition),
      },
    });
    vi.mocked(fetch).mockImplementation(
      async (url) =>
        ({
          ok: true,
          json: async () =>
            String(url).includes("reverse")
              ? { label: "Andheri West, Mumbai" }
              : DELHI_PLAN_FIXTURE,
        }) as Response,
    );
    render(<App initialView="dashboard" />);
    await user.click(
      screen.getByRole("button", { name: /Use My Live Location/i }),
    );
    await screen.findByRole("tab", { name: /Overview/i });
    await user.click(
      screen.getByRole("radio", { name: /South Delhi Joint Family/i }),
    );
    await waitFor(() =>
      expect(
        screen.getByRole("radio", { name: /South Delhi Joint Family/i }),
      ).toHaveAttribute("aria-checked", "true"),
    );
    const requests = vi
      .mocked(fetch)
      .mock.calls.filter(([url]) => url === "/api/plan/daily");
    expect(JSON.parse(String(requests[0]?.[1]?.body))).toMatchObject(
      coordinates,
    );
    expect(
      JSON.parse(String(requests[requests.length - 1]?.[1]?.body)),
    ).toMatchObject({
      city: "Andheri West, Mumbai",
      ...coordinates,
      household_preset_id: "south-delhi",
    });
  });

  it("submits manual stops through the daily plan and displays the applied timing and factor", async () => {
    const user = userEvent.setup();
    render(<App initialView="dashboard" />);
    await user.click(screen.getByRole("button", { name: /^Delhi$/i }));
    await user.click(await screen.findByRole("tab", { name: /Routine/i }));
    for (const [index, name, distance, duration] of [
      [1, "Pharmacy", "1", "5"],
      [2, "Groceries", "2", "10"],
    ] as const) {
      await user.click(
        await screen.findByRole("button", { name: "Add errand" }),
      );
      fireEvent.change(screen.getByLabelText(`Stop ${index} name`), {
        target: { value: name },
      });
      fireEvent.change(
        screen.getByLabelText(`Stop ${index} distance from home (km)`),
        { target: { value: distance } },
      );
      fireEvent.change(screen.getByLabelText(`Stop ${index} duration (min)`), {
        target: { value: duration },
      });
    }
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        ...DELHI_PLAN_FIXTURE,
        errand_merger: {
          ...DELHI_PLAN_FIXTURE.errand_merger,
          baseline_separate_distance_km: 6,
          merged_loop_distance_km: 4.4,
          distance_saved_km: 1.6,
          tailpipe_co2_saved_grams: 76.8,
          recommended_start_hour: 13.25,
          recommended_end_hour: 13.676,
          travel_mode: "petrol_2w",
          emissions_factor_g_per_km: 48,
        },
      }),
    } as Response);
    await user.click(screen.getByRole("button", { name: "Apply errands" }));
    const request = vi.mocked(fetch).mock.lastCall?.[1];
    expect(JSON.parse(String(request?.body)).errands).toEqual([
      expect.objectContaining({
        name: "Pharmacy",
        distance_from_home_km: 1,
        duration_minutes: 5,
      }),
      expect.objectContaining({
        name: "Groceries",
        distance_from_home_km: 2,
        duration_minutes: 10,
      }),
    ]);
    expect(await screen.findByText("13:15–13:41")).toBeInTheDocument();
    await user.click(
      screen.getByRole("button", { name: /Show the Math.*errand/i }),
    );
    expect(screen.getByText(/1.6 km × 48 g\/km = 76.8 g/)).toBeInTheDocument();
  });

  it("retries a failed room submission and ignores an older response without reloading the schedule", async () => {
    const user = userEvent.setup();
    render(<App initialView="dashboard" />);
    await user.click(screen.getByRole("button", { name: /^Delhi$/i }));
    await user.click(await screen.findByRole("tab", { name: /Indoor/i }));

    const length = await screen.findByLabelText("Length (m)");
    const submit = screen.getByRole("button", { name: /Update CADR/i });
    const roomResponse = (
      lengthM: number,
      volume: number,
      cadr: number,
      cfm: number,
    ) =>
      ({
        ok: true,
        json: async () => ({
          ...DELHI_PLAN_FIXTURE.room_cadr_guidance,
          dimensions: { length_m: lengthM, width_m: 4, height_m: 2.8 },
          room_volume_m3: volume,
          required_cadr_m3_per_hr: cadr,
          required_cadr_cfm: cfm,
        }),
      }) as Response;

    vi.mocked(fetch).mockResolvedValueOnce({
      ok: false,
      status: 503,
    } as Response);
    fireEvent.change(length, { target: { value: "6" } });
    await user.click(submit);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Room sizing could not be updated.",
    );
    expect(screen.getByText(/Sized for 56 m³/)).toBeInTheDocument();
    vi.mocked(fetch).mockResolvedValueOnce(roomResponse(6, 67.2, 336, 197.76));
    await user.click(
      screen.getByRole("button", { name: "Retry room calculation" }),
    );
    expect(await screen.findByText(/Sized for 67.2 m³/)).toBeInTheDocument();
    expect(screen.getByText(/197.76 CFM/)).toBeInTheDocument();

    let respondOlder: (response: Response) => void = () => {};
    vi.mocked(fetch).mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          respondOlder = resolve;
        }),
    );
    fireEvent.change(length, { target: { value: "7" } });
    await user.click(submit);
    vi.mocked(fetch).mockResolvedValueOnce(roomResponse(8, 89.6, 448, 263.68));
    fireEvent.change(length, { target: { value: "8" } });
    await user.click(submit);
    expect(await screen.findByText(/Sized for 89.6 m³/)).toBeInTheDocument();
    await act(async () => respondOlder(roomResponse(7, 78.4, 392, 230.72)));
    expect(screen.getByText(/Sized for 89.6 m³/)).toBeInTheDocument();
    expect(
      vi.mocked(fetch).mock.calls.filter(([url]) => url === "/api/plan/daily"),
    ).toHaveLength(1);
  });

  it("renders main landmarks: header, main content, and footer", async () => {
    await act(async () => {
      render(<App />);
    });

    expect(screen.getByRole("banner")).toBeInTheDocument();
    expect(screen.getByRole("main")).toBeInTheDocument();
    expect(screen.getByRole("contentinfo")).toBeInTheDocument();
  });

  it("contains skip link targeting #main-content", async () => {
    await act(async () => {
      render(<App />);
    });

    const skipLink = screen.getByText(/Skip to main content/i);
    expect(skipLink).toBeInTheDocument();
    expect(skipLink).toHaveAttribute("href", "#main-content");
  });

  it("has an aria-live region for polite announcements", async () => {
    await act(async () => {
      render(<App />);
    });

    const liveRegion = screen.getByTestId("aqi-category-live-region");
    expect(liveRegion).toBeInTheDocument();
    expect(liveRegion).toHaveAttribute("aria-live", "polite");
  });

  it("navigates from landing to 4-tab dashboard when Get Started is clicked and returns to landing on brand click", async () => {
    const user = userEvent.setup();
    await act(async () => {
      render(<App initialView="landing" />);
    });

    // Landing view is active
    const getStartedBtn = screen.getByRole("button", { name: /Get Started/i });
    await user.click(getStartedBtn);

    expect(
      await screen.findByRole("heading", { name: /Choose your location/i }),
    ).toBeInTheDocument();
    expect(fetch).not.toHaveBeenCalled();
    await user.click(screen.getByRole("button", { name: /^Noida$/i }));

    // Dashboard appears only after an explicitly selected location and successful fetch.
    expect(
      await screen.findByRole("tablist", {
        name: /Urbero Workspace Sections/i,
      }),
    ).toBeInTheDocument();
    expect(
      screen
        .getAllByRole("radio")
        .every((radio) => radio.getAttribute("aria-checked") === "false"),
    ).toBe(true);
    await user.click(
      screen.getByRole("radio", { name: /Andheri Mumbai Working Couple/i }),
    );
    const calls = vi.mocked(fetch).mock.calls;
    const payload = JSON.parse(String(calls[calls.length - 1][1]?.body));
    expect(payload.latitude).toBe(28.5355);
    expect(payload.longitude).toBe(77.391);
    expect(payload.household_preset_id).toBe("mumbai-couple");

    // Click brand mark to return to landing
    const brandBtn = screen.getByRole("button", {
      name: /Return to Urbero Home/i,
    });
    await user.click(brandBtn);

    // Back in landing view
    expect(
      await screen.findByRole("button", { name: /Get Started/i }),
    ).toBeInTheDocument();
  });

  it("submits a custom activity with exact times and keeps the Routine tab open", async () => {
    const user = userEvent.setup();
    render(<App initialView="dashboard" />);
    await user.click(screen.getByRole("button", { name: /^Noida$/i }));
    await user.click(await screen.findByRole("tab", { name: /Routine/i }));
    await user.click(
      await screen.findByRole("button", { name: "Add activity" }),
    );
    await user.type(screen.getByLabelText("Activity name"), "School pickup");
    fireEvent.change(screen.getByLabelText("Start time"), {
      target: { value: "07:45" },
    });
    fireEvent.change(screen.getByLabelText("End time"), {
      target: { value: "08:15" },
    });
    await user.click(screen.getByLabelText("Fixed time"));
    await user.click(screen.getByRole("button", { name: "Apply schedule" }));
    const requests = vi.mocked(fetch).mock.calls;
    expect(
      JSON.parse(String(requests[requests.length - 1][1]?.body)).activities,
    ).toMatchObject([
      {
        name: "School pickup",
        scheduled_start_hour: 7.75,
        scheduled_end_hour: 8.25,
        is_flexible: false,
      },
    ]);
    expect(screen.getByRole("tab", { name: /Routine/i })).toHaveAttribute(
      "aria-selected",
      "true",
    );
  });

  it("sends a travel question for the selected location and displays the validated suggestion", async () => {
    const user = userEvent.setup();
    render(<App initialView="dashboard" />);
    await user.click(screen.getByRole("button", { name: /^Noida$/i }));
    await user.click(await screen.findByRole("tab", { name: /Routine/i }));
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        priority: "balance",
        source: "grok",
        smog_advisory: "",
        recommendation: {
          label: "Public Bus",
          distance_km: 4,
          duration_minutes: 15,
          tailpipe_co2_grams: 140,
          personal_inhaled_pm25_ug: 10,
        },
      }),
    } as Response);
    await user.type(
      await screen.findByLabelText("Travel question"),
      "I prefer public transport",
    );
    fireEvent.change(screen.getByLabelText("Trip distance (km)"), {
      target: { value: "4" },
    });
    await user.click(screen.getByRole("button", { name: "Get travel advice" }));
    expect(await screen.findByText("Consider Public Bus")).toBeInTheDocument();
    const requests = vi.mocked(fetch).mock.calls;
    const [url, options] = requests[requests.length - 1];
    expect(url).toBe("/api/exposure/commute/advice");
    expect(JSON.parse(String(options?.body))).toMatchObject({
      latitude: 28.5355,
      longitude: 77.391,
      distance_km: 4,
      question: "I prefer public transport",
    });
  });

  it("full page has zero accessibility violations via jest-axe on landing view", async () => {
    let container: HTMLElement;
    await act(async () => {
      const renderRes = render(<App initialView="landing" />);
      container = renderRes.container;
    });

    const results = await axe(container!);
    expect(results).toHaveNoViolations();
  });

  it("full page has zero accessibility violations via jest-axe on dashboard view", async () => {
    let container: HTMLElement;
    await act(async () => {
      const renderRes = render(<App initialView="dashboard" />);
      container = renderRes.container;
    });

    const results = await axe(container!);
    expect(results).toHaveNoViolations();
  });
});
