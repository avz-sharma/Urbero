import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "jest-axe";
import { LocationPicker } from "../components/LocationPicker";
import type { ActiveLocation, LocationSearchResult } from "../api/types";

describe("LocationPicker Component & Accessibility", () => {
  const defaultLocation: ActiveLocation = {
    label: "South Delhi, Delhi",
    lat: 28.6139,
    lon: 77.209,
    origin: "preset",
  };

  const mockOnSelectLocation = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  function mockGps() {
    const position = { coords: { latitude: 28.6123, longitude: 77.2087 } };
    const geolocation = {
      getCurrentPosition: vi.fn((success: (result: typeof position) => void) =>
        success(position),
      ),
    };
    vi.stubGlobal("navigator", { ...navigator, geolocation });
  }

  it.each([
    ["success", "Connaught Place, Delhi"],
    ["non-2xx response", "Current Location"],
    ["network error", "GPS Location"],
  ])("selects the GPS coordinates after a %s", async (outcome, label) => {
    mockGps();
    const reverseGeocode = vi.fn();
    if (outcome === "success") {
      reverseGeocode.mockResolvedValue(Response.json({ label, city: "Delhi" }));
    } else if (outcome === "non-2xx response") {
      reverseGeocode.mockResolvedValue(new Response(null, { status: 503 }));
    } else {
      reverseGeocode.mockRejectedValue(new Error("Network unavailable"));
    }
    vi.stubGlobal("fetch", reverseGeocode);
    render(
      <LocationPicker
        activeLocation={null}
        gate
        onSelectLocation={mockOnSelectLocation}
      />,
    );

    await userEvent.setup().click(
      screen.getByRole("button", { name: "Use My Live Location" }),
    );

    expect(reverseGeocode.mock.calls[0][0]).toBe(
      "/api/locations/reverse?lat=28.61&lon=77.21",
    );
    expect(mockOnSelectLocation.mock.calls).toEqual([
      [{ label, lat: 28.6123, lon: 77.2087, origin: "gps" }],
    ]);
  });

  it("keeps a manual selection when an older GPS response finishes parsing", async () => {
    mockGps();
    let finishGps: (data: { label: string }) => void = () => {};
    const reverseBody = new Promise<{ label: string }>((resolve) => {
      finishGps = resolve;
    });
    const parseGps = vi.fn(() => reverseBody);
    const reverseGeocode = vi.fn().mockResolvedValue({ ok: true, json: parseGps });
    vi.stubGlobal("fetch", reverseGeocode);
    const user = userEvent.setup();
    render(
      <LocationPicker
        activeLocation={null}
        gate
        onSelectLocation={mockOnSelectLocation}
      />,
    );

    await user.click(
      screen.getByRole("button", { name: "Use My Live Location" }),
    );
    expect(parseGps).toHaveBeenCalledTimes(1);
    await user.click(screen.getByRole("button", { name: "Noida" }));
    expect(reverseGeocode).toHaveBeenCalledTimes(1);
    expect(reverseGeocode.mock.calls[0][1].signal.aborted).toBe(true);
    await act(async () => finishGps({ label: "Connaught Place, Delhi" }));

    expect(mockOnSelectLocation.mock.calls).toEqual([
      [
        {
          label: "Noida (Sector 62)",
          lat: 28.5355,
          lon: 77.391,
          origin: "search",
        },
      ],
    ]);
    expect(
      screen.getByRole("button", { name: "Use My Live Location" }),
    ).toBeEnabled();
  });

  it("renders trigger pill with label, distance, and live badge", () => {
    render(
      <LocationPicker
        activeLocation={defaultLocation}
        stationDistanceKm={4.8}
        stationStatus="live"
        onSelectLocation={mockOnSelectLocation}
      />,
    );

    const trigger = screen.getByRole("button", { name: /Change location/i });
    expect(trigger).toBeInTheDocument();
    expect(screen.getByText("South Delhi, Delhi")).toBeInTheDocument();
    expect(screen.getByText("(4.8 km)")).toBeInTheDocument();
    expect(screen.getByText("live")).toBeInTheDocument();
  });

  it("opens popover modal on click and renders Use My Location and Quick City Chips", async () => {
    const user = userEvent.setup();
    render(
      <LocationPicker
        activeLocation={defaultLocation}
        stationDistanceKm={4.8}
        onSelectLocation={mockOnSelectLocation}
      />,
    );

    await user.click(screen.getByRole("button", { name: /Change location/i }));

    expect(
      screen.getByRole("dialog", { name: /Location Search and Geolocation/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Use My Location/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("combobox")).toBeInTheDocument();
    expect(screen.getByText("Delhi")).toBeInTheDocument();
    expect(screen.getByText("Noida")).toBeInTheDocument();
  });

  it("selects a quick city chip and notifies parent callback", async () => {
    const user = userEvent.setup();
    render(
      <LocationPicker
        activeLocation={defaultLocation}
        stationDistanceKm={4.8}
        onSelectLocation={mockOnSelectLocation}
      />,
    );

    await user.click(screen.getByRole("button", { name: /Change location/i }));
    await user.click(screen.getByRole("button", { name: /Noida/i }));

    expect(mockOnSelectLocation).toHaveBeenCalledWith(
      expect.objectContaining({
        label: expect.stringContaining("Noida"),
        lat: 28.5355,
        lon: 77.391,
        origin: "search",
      }),
    );
  });

  it("handles geolocation PERMISSION_DENIED cleanly inline without alert()", async () => {
    const user = userEvent.setup();

    // Mock geolocation error with PERMISSION_DENIED (code 1)
    const mockGeolocation = {
      getCurrentPosition: vi.fn((_success, error) => {
        error({
          code: 1,
          PERMISSION_DENIED: 1,
          POSITION_UNAVAILABLE: 2,
          TIMEOUT: 3,
          message: "User denied Geolocation",
        });
      }),
    };
    vi.stubGlobal("navigator", { ...navigator, geolocation: mockGeolocation });

    render(
      <LocationPicker
        activeLocation={defaultLocation}
        onSelectLocation={mockOnSelectLocation}
      />,
    );

    await user.click(screen.getByRole("button", { name: /Change location/i }));
    await user.click(screen.getByRole("button", { name: /Use My Location/i }));

    expect(
      screen.getByText(
        /Location access blocked\. Search any Indian city or locality below\./i,
      ),
    ).toBeInTheDocument();
  });

  it("handles geolocation TIMEOUT cleanly inline without alert()", async () => {
    const user = userEvent.setup();

    const mockGeolocation = {
      getCurrentPosition: vi.fn((_success, error) => {
        error({
          code: 3,
          PERMISSION_DENIED: 1,
          POSITION_UNAVAILABLE: 2,
          TIMEOUT: 3,
          message: "Timeout expired",
        });
      }),
    };
    vi.stubGlobal("navigator", { ...navigator, geolocation: mockGeolocation });

    render(
      <LocationPicker
        activeLocation={defaultLocation}
        onSelectLocation={mockOnSelectLocation}
      />,
    );

    await user.click(screen.getByRole("button", { name: /Change location/i }));
    await user.click(screen.getByRole("button", { name: /Use My Location/i }));

    expect(
      screen.getByText(/Couldn't detect GPS\. Enter your area manually\./i),
    ).toBeInTheDocument();
  });

  it("debounces search input by 300ms and navigates with keyboard", async () => {
    const user = userEvent.setup();

    const mockSearchResults = [
      {
        label: "Sector 62, Noida, Uttar Pradesh",
        city: "Noida",
        state: "Uttar Pradesh",
        lat: 28.627,
        lon: 77.362,
      },
      {
        label: "Sector 63, Noida, Uttar Pradesh",
        city: "Noida",
        state: "Uttar Pradesh",
        lat: 28.634,
        lon: 77.371,
      },
    ];

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockSearchResults,
      }),
    );

    render(
      <LocationPicker
        activeLocation={defaultLocation}
        onSelectLocation={mockOnSelectLocation}
      />,
    );

    await user.click(screen.getByRole("button", { name: /Change location/i }));

    const input = screen.getByRole("combobox");
    expect(input).toHaveFocus();
    await user.type(input, "Sector 62");

    await waitFor(() => {
      expect(screen.getByRole("listbox")).toBeInTheDocument();
    });

    expect(
      screen.getByText("Sector 62, Noida, Uttar Pradesh"),
    ).toBeInTheDocument();

    // From no active option, ArrowUp wraps to the end of the list.
    await user.keyboard("{ArrowUp}");
    expect(screen.getByRole("option", { selected: true })).toHaveTextContent(
      "Sector 63, Noida, Uttar Pradesh",
    );
    await user.keyboard("{ArrowDown}");
    await user.keyboard("{Enter}");

    expect(mockOnSelectLocation).toHaveBeenCalledWith(
      expect.objectContaining({
        label: "Sector 62, Noida, Uttar Pradesh",
        lat: 28.627,
        lon: 77.362,
        origin: "search",
      }),
    );
  });

  it("has zero accessibility violations via jest-axe when opened", async () => {
    const user = userEvent.setup();
    const { container } = render(
      <LocationPicker
        activeLocation={defaultLocation}
        stationDistanceKm={5.2}
        stationStatus="live"
        onSelectLocation={mockOnSelectLocation}
      />,
    );

    await user.click(screen.getByRole("button", { name: /Change location/i }));

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it("ignores a superseded search even if its response was already parsing", async () => {
    const user = userEvent.setup();
    const stale = {
      label: "Stale result",
      city: "Delhi",
      state: "Delhi",
      lat: 28.6,
      lon: 77.2,
    };
    const fresh = {
      label: "Fresh result",
      city: "Noida",
      state: "Uttar Pradesh",
      lat: 28.5,
      lon: 77.4,
    };
    let finishStale: (data: LocationSearchResult[]) => void = () => {};
    const staleBody = new Promise<LocationSearchResult[]>((resolve) => {
      finishStale = resolve;
    });
    const parsing = vi.fn(() => staleBody);
    const fetchSearch = vi
      .fn()
      .mockResolvedValueOnce({ ok: true, json: parsing })
      .mockResolvedValueOnce({ ok: true, json: async () => [fresh] });
    vi.stubGlobal("fetch", fetchSearch);
    render(
      <LocationPicker
        activeLocation={null}
        gate
        onSelectLocation={mockOnSelectLocation}
      />,
    );
    const input = screen.getByRole("combobox");
    await user.type(input, "Delhi");
    await waitFor(() => expect(parsing).toHaveBeenCalled());
    await user.clear(input);
    await user.type(input, "Noida");
    expect(fetchSearch.mock.calls[0][1].signal.aborted).toBe(true);
    await screen.findByText(fresh.label);
    await act(async () => {
      finishStale([stale]);
    });
    expect(screen.queryByText(stale.label)).not.toBeInTheDocument();
    expect(screen.getByText(fresh.label)).toBeInTheDocument();
  });
});
