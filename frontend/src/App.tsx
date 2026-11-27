import { useState, useEffect, useRef } from "react";
import { LazyMotion, domAnimation, MotionConfig } from "motion/react";
import { Sun, Moon } from "lucide-react";
import { INDIAN_PRESETS, type PresetProfile } from "./HouseholdProfile";
import { useTheme } from "./lib/useTheme";
import { LightRays } from "./components/ui/LightRays";
import { LandingView } from "./components/LandingView";
import { DashboardShell } from "./components/DashboardShell";
import { LocationPicker } from "./components/LocationPicker";
import type {
  ActiveLocation,
  DailyPlanRequest,
  DailyPlanResponse,
  ErrandStop,
  RoomCADRResult,
  RoomDimensions,
  RoomIndoorFactors,
  ScheduledActivity,
} from "./api/types";

export interface AppProps {
  initialView?: "landing" | "dashboard";
}

type RoomSubmission = {
  dimensions: RoomDimensions;
  factors: RoomIndoorFactors;
  targetAch: number;
};

export const App = ({ initialView = "landing" }: AppProps) => {
  const [theme, toggleTheme] = useTheme();
  const [view, setView] = useState(initialView);
  const [activeLocation, setActiveLocation] = useState<ActiveLocation | null>(
    null,
  );
  const [selectedPresetId, setSelectedPresetId] = useState<string | null>(null);
  const selectedPreset =
    INDIAN_PRESETS.find((p) => p.id === selectedPresetId) ?? null;
  const [planData, setPlanData] = useState<DailyPlanResponse | null>(null);
  const [activities, setActivities] = useState<ScheduledActivity[]>([]);
  const [errands, setErrands] = useState<ErrandStop[]>([]);
  const acceptedErrands = useRef<ErrandStop[]>([]);
  const [errandError, setErrandError] = useState<string | null>(null);
  const lastLocation = useRef<ActiveLocation | null>(null);
  const lastSuccessfulLocation = useRef<ActiveLocation | null>(null);
  const [roomOverride, setRoomOverride] = useState<RoomCADRResult | null>(null);
  const [failedRoom, setFailedRoom] = useState<RoomSubmission | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [retry, setRetry] = useState(0);
  const [isFetching, setIsFetching] = useState(false);
  const [announcement, setAnnouncement] = useState("");
  const previousCategory = useRef<string | null>(null);
  const mainRef = useRef<HTMLElement>(null);
  const locationGateRef = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    if (view === "dashboard" && !activeLocation)
      locationGateRef.current?.focus();
  }, [view, activeLocation]);
  const cadrSequence = useRef(0);

  useEffect(() => {
    if (!activeLocation || view !== "dashboard") {
      setIsFetching(false);
      return;
    }
    const locationChanged = lastLocation.current !== activeLocation;
    lastLocation.current = activeLocation;
    if (locationChanged) cadrSequence.current += 1;
    const controller = new AbortController();
    setIsFetching(true);
    setError(null);
    setErrandError(null);
    if (locationChanged) {
      setPlanData(null);
      setRoomOverride(null);
      setFailedRoom(null);
    }
    const payload: DailyPlanRequest = {
      city: activeLocation.label.trim().slice(0, 160),
      latitude: activeLocation.lat,
      longitude: activeLocation.lon,
      household_preset_id: selectedPresetId,
      language_preference: "english",
      commute_distance_km: selectedPreset?.commute_distance_km ?? 12,
      activities,
      errands,
      ...(selectedPreset && {
        room_dimensions: selectedPreset.room_dimensions,
        indoor_factors: selectedPreset.indoor_factors,
        commute_distance_km: selectedPreset.commute_distance_km,
      }),
    };
    void (async () => {
      try {
        const response = await fetch("/api/plan/daily", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          signal: controller.signal,
          body: JSON.stringify(payload),
        });
        if (response.status === 422 && errands.length && !locationChanged) {
          const errorBody: { detail?: unknown } = await response.json();
          if (
            errorBody.detail ===
              "No feasible errand loop in the available window. Adjust stop times." &&
            !controller.signal.aborted
          ) {
            setErrandError(
              "No loop fits the stop times. Adjust opening or finish times, or remove a stop and apply again.",
            );
            return;
          }
        }
        if (!response.ok)
          throw new Error(
            "Air quality is temporarily unavailable. Please retry or choose another location.",
          );
        const data: DailyPlanResponse = await response.json();
        if (controller.signal.aborted) return;
        acceptedErrands.current = errands;
        setPlanData(data);
        if (previousCategory.current !== data.aqi_result.category) {
          setAnnouncement(
            `Air quality category updated to ${data.aqi_result.category}.`,
          );
          previousCategory.current = data.aqi_result.category;
        }
        if (lastSuccessfulLocation.current !== activeLocation) {
          lastSuccessfulLocation.current = activeLocation;
          mainRef.current?.focus();
        }
      } catch {
        if (!controller.signal.aborted)
          setError(
            "Air quality is temporarily unavailable. Please retry or choose another location.",
          );
      } finally {
        if (!controller.signal.aborted) setIsFetching(false);
      }
    })();
    return () => controller.abort();
  }, [
    activeLocation,
    activities,
    errands,
    selectedPreset,
    selectedPresetId,
    view,
    retry,
  ]);

  const selectPreset = (preset: PresetProfile) => {
    setSelectedPresetId(preset.id);
    setActivities(preset.activities);
    cadrSequence.current += 1;
    setRoomOverride(null);
    setFailedRoom(null);
  };

  const selectLocation = (location: ActiveLocation) => {
    cadrSequence.current += 1;
    acceptedErrands.current = [];
    setErrands([]);
    setActiveLocation(location);
  };

  const recalculateCADR = async (
    dimensions: RoomDimensions,
    factors: RoomIndoorFactors,
    targetAch: number,
  ) => {
    const sequence = ++cadrSequence.current;
    setFailedRoom(null);
    try {
      const response = await fetch(
        `/api/exposure/cadr?target_ach=${targetAch}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ dimensions, factors }),
        },
      );
      if (!response.ok) throw new Error("CADR unavailable");
      const result: RoomCADRResult = await response.json();
      if (sequence === cadrSequence.current) setRoomOverride(result);
    } catch {
      if (sequence === cadrSequence.current)
        setFailedRoom({ dimensions, factors, targetAch });
    }
  };

  return (
    <LazyMotion features={domAnimation} strict>
      <MotionConfig reducedMotion="user">
        <div className="relative min-h-screen bg-[var(--bg-canvas)] text-[var(--text-primary)] flex flex-col font-sans">
          <LightRays
            color={
              theme === "dark"
                ? "rgba(45, 212, 191, 0.22)"
                : "rgba(15, 118, 110, 0.14)"
            }
          />
          <a
            href="#main-content"
            className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:p-4 focus:bg-teal-700 focus:text-white"
          >
            Skip to main content
          </a>
          <div
            aria-live="polite"
            aria-atomic="true"
            className="sr-only"
            data-testid="aqi-category-live-region"
          >
            {announcement}
          </div>
          <header className="relative z-40 border-b border-[var(--border-subtle)] bg-[var(--bg-surface)] p-4">
            <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-3">
              <button
                type="button"
                aria-label="Return to Urbero Home"
                onClick={() => setView("landing")}
                className="min-h-[44px] font-bold text-xl"
              >
                Urbero
              </button>
              <div className="flex gap-3 items-center">
                {activeLocation && (
                  <LocationPicker
                    activeLocation={activeLocation}
                    onSelectLocation={selectLocation}
                    stationDistanceKm={planData?.station_metadata.distance_km}
                    stationStatus={planData?.station_metadata.status}
                    isLoading={isFetching}
                  />
                )}
                {view === "landing" && (
                  <button
                    type="button"
                    onClick={() => setView("dashboard")}
                    className="min-h-[44px] px-3"
                  >
                    Open Workspace
                  </button>
                )}
                <button
                  type="button"
                  onClick={toggleTheme}
                  aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
                  className="min-h-[44px] min-w-[44px] p-3 rounded-xl border border-[var(--border-subtle)]"
                >
                  {theme === "dark" ? (
                    <Sun aria-hidden="true" />
                  ) : (
                    <Moon aria-hidden="true" />
                  )}
                </button>
              </div>
            </div>
          </header>
          <main
            id="main-content"
            ref={mainRef}
            tabIndex={-1}
            aria-busy={isFetching}
            className="relative z-10 max-w-7xl mx-auto p-4 sm:p-6 space-y-6 flex-1 w-full"
          >
            {view === "landing" ? (
              <LandingView onGetStarted={() => setView("dashboard")} />
            ) : !activeLocation ? (
              <section
                id="tab-overview"
                aria-labelledby="location-gate-title"
                className="max-w-xl mx-auto py-8 space-y-5"
              >
                <h1
                  id="location-gate-title"
                  ref={locationGateRef}
                  tabIndex={-1}
                  className="text-3xl font-bold"
                >
                  Choose your location
                </h1>
                <p>
                  Start with your area for relevant air quality and daily
                  guidance. Household presets are optional.
                </p>
                <LocationPicker
                  gate
                  activeLocation={null}
                  onSelectLocation={selectLocation}
                />
              </section>
            ) : (
              <>
                {error && (
                  <div role="alert" className="p-4 border rounded-xl">
                    <p>{error}</p>
                    <button
                      type="button"
                      onClick={() => setRetry((n) => n + 1)}
                      className="min-h-[44px] px-3 underline"
                    >
                      Retry
                    </button>
                  </div>
                )}
                {isFetching && (
                  <p>Loading air quality for {activeLocation.label}…</p>
                )}
                {planData && (
                  <DashboardShell
                    planData={planData}
                    selectedPreset={selectedPreset}
                    onSelectPreset={selectPreset}
                    activeLocation={activeLocation}
                    activities={activities}
                    onApplySchedule={(schedule) => {
                      setErrands(acceptedErrands.current);
                      setActivities(schedule);
                    }}
                    updatingSchedule={isFetching}
                    errands={errands}
                    onApplyErrands={setErrands}
                    errandError={errandError}
                    cadrGuidance={roomOverride ?? planData.room_cadr_guidance}
                    onRecalculateCADR={recalculateCADR}
                    roomError={
                      failedRoom ? "Room sizing could not be updated." : null
                    }
                    onRetryRoom={
                      failedRoom
                        ? () =>
                            void recalculateCADR(
                              failedRoom.dimensions,
                              failedRoom.factors,
                              failedRoom.targetAch,
                            )
                        : undefined
                    }
                  />
                )}
              </>
            )}
          </main>
          <footer className="relative z-10 border-t border-[var(--border-subtle)] bg-[var(--bg-surface)] py-5 text-center text-xs">
            Urbero · Indian cities · CPCB breakpoint estimates · WAQI / CPCB and
            Open-Meteo / CAMS
          </footer>
        </div>
      </MotionConfig>
    </LazyMotion>
  );
};

export default App;
