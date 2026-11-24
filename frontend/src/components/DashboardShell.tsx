import React, { useState, useRef } from "react";
import { m, AnimatePresence, useReducedMotion } from "motion/react";
import {
  Users,
  CalendarClock,
  Wind,
  FileText,
  Route,
  Navigation,
  MapPin,
  type LucideIcon,
} from "lucide-react";
import type {
  ActiveLocation,
  DailyPlanResponse,
  RoomCADRResult,
  RoomDimensions,
  RoomIndoorFactors,
  ScheduledActivity,
} from "../api/types";
import { HouseholdProfile, type PresetProfile } from "../HouseholdProfile";
import { LowEmissionRoutine, BriefingCards } from "../LowEmissionRoutine";
import { IndoorAirGuide } from "../IndoorAirGuide";
import { ImpactJustification } from "../ImpactJustification";
import { snappySpring } from "../lib/motion";
import { MathDrawer } from "../common/MathDrawer";
import { RecommendationCards } from "../common/RecommendationCards";
import { ScheduleEditor } from "../LowEmissionRoutine/ScheduleEditor";
import { TravelAdvice } from "../LowEmissionRoutine/TravelAdvice";

export interface DashboardShellProps {
  planData: DailyPlanResponse;
  selectedPreset: PresetProfile | null;
  onSelectPreset: (preset: PresetProfile) => void;
  activeLocation: ActiveLocation;
  activities?: ScheduledActivity[];
  onApplySchedule?: (activities: ScheduledActivity[]) => void;
  updatingSchedule?: boolean;
  cadrGuidance: RoomCADRResult;
  onRecalculateCADR: (
    dimensions: RoomDimensions,
    factors: RoomIndoorFactors,
    targetAch: number,
  ) => void;
}

interface TabDef {
  id: string;
  label: string;
  shortLabel: string;
  icon: LucideIcon;
}

const TABS: TabDef[] = [
  {
    id: "tab-overview",
    label: "1. Overview & Family",
    shortLabel: "Overview",
    icon: Users,
  },
  {
    id: "tab-routine",
    label: "2. Routine & Commute",
    shortLabel: "Routine",
    icon: CalendarClock,
  },
  {
    id: "tab-indoor",
    label: "3. Indoor Air & CADR",
    shortLabel: "Indoor CADR",
    icon: Wind,
  },
  {
    id: "tab-briefings",
    label: "4. Briefings & Impact",
    shortLabel: "Briefings",
    icon: FileText,
  },
];

export const DashboardShell: React.FC<DashboardShellProps> = ({
  planData,
  selectedPreset,
  onSelectPreset,
  activeLocation,
  activities = [],
  onApplySchedule,
  updatingSchedule = false,
  cadrGuidance,
  onRecalculateCADR,
}) => {
  const [activeTab, setActiveTab] = useState<number>(0);
  const [direction, setDirection] = useState<number>(1);
  const reducedMotion = useReducedMotion();
  const tabListRef = useRef<HTMLDivElement>(null);

  const handleTabChange = (newIndex: number) => {
    if (newIndex === activeTab) return;
    setDirection(newIndex > activeTab ? 1 : -1);
    setActiveTab(newIndex);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    let next = activeTab;
    if (e.key === "ArrowRight") {
      e.preventDefault();
      next = (activeTab + 1) % TABS.length;
      handleTabChange(next);
    } else if (e.key === "ArrowLeft") {
      e.preventDefault();
      const prev = (activeTab - 1 + TABS.length) % TABS.length;
      next = prev;
      handleTabChange(prev);
    } else if (e.key === "Home") {
      e.preventDefault();
      handleTabChange(0);
      next = 0;
    } else if (e.key === "End") {
      e.preventDefault();
      handleTabChange(TABS.length - 1);
      next = TABS.length - 1;
    }
    if (next !== activeTab) {
      const tabs =
        tabListRef.current?.querySelectorAll<HTMLButtonElement>('[role="tab"]');
      tabs?.[next]?.focus();
    }
  };

  const errandsResult = planData.errand_merger;

  return (
    <div className="space-y-6">
      {/* Accessible Horizontal Tab Bar (role="tablist") */}
      <div
        ref={tabListRef}
        role="tablist"
        aria-label="Urbero Workspace Sections"
        onKeyDown={handleKeyDown}
        className="flex items-center gap-1.5 p-1.5 bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded-2xl overflow-x-auto shadow-2xs"
      >
        {TABS.map((tab, idx) => {
          const isSelected = activeTab === idx;
          const IconComponent = tab.icon;

          return (
            <button
              key={tab.id}
              id={tab.id}
              type="button"
              role="tab"
              aria-selected={isSelected}
              aria-controls={`tabpanel-${idx}`}
              tabIndex={isSelected ? 0 : -1}
              onClick={() => handleTabChange(idx)}
              className={`relative z-10 flex-1 min-h-[44px] px-3.5 py-2 text-xs font-bold rounded-xl transition-colors focus:outline-none focus:ring-2 focus:ring-teal-500 inline-flex items-center justify-center gap-2 cursor-pointer whitespace-nowrap ${
                isSelected
                  ? "text-white dark:text-[#042F2E]"
                  : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface)]/50"
              }`}
            >
              {isSelected && (
                <m.div
                  layoutId="active-workspace-tab"
                  transition={snappySpring}
                  className="absolute inset-0 bg-[#0F766E] dark:bg-[#2DD4BF] rounded-xl -z-10 shadow-xs"
                />
              )}
              <IconComponent
                className="w-4 h-4 shrink-0"
                strokeWidth={1.75}
                aria-hidden="true"
              />
              <span className="hidden sm:inline">{tab.label}</span>
              <span className="inline sm:hidden">{tab.shortLabel}</span>
            </button>
          );
        })}
      </div>

      {/* Directional Animated Tab Panel Container */}
      <AnimatePresence mode="wait" custom={direction}>
        <m.div
          key={activeTab}
          id={`tabpanel-${activeTab}`}
          role="tabpanel"
          aria-labelledby={TABS[activeTab].id}
          custom={direction}
          initial={reducedMotion ? false : { opacity: 0, x: direction * 24 }}
          animate={{ opacity: 1, x: 0 }}
          exit={reducedMotion ? undefined : { opacity: 0, x: -direction * 24 }}
          transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
          className="focus:outline-none space-y-6"
        >
          {/* TAB 1: Overview & Family */}
          {activeTab === 0 && (
            <div className="space-y-6">
              {/* Quick Location Trigger Bar */}
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 p-3.5 bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl shadow-2xs">
                <div className="flex items-center gap-2.5">
                  <span className="p-2 rounded-xl bg-teal-50 text-teal-700 dark:bg-teal-950 dark:text-teal-400">
                    <MapPin
                      className="w-4 h-4"
                      strokeWidth={2}
                      aria-hidden="true"
                    />
                  </span>
                  <div>
                    <div className="text-xs font-bold text-[var(--text-primary)]">
                      Current Area:{" "}
                      <span className="text-teal-700 dark:text-teal-400 font-extrabold">
                        {activeLocation.label}
                      </span>
                    </div>
                    <div className="text-[11px] text-[var(--text-secondary)]">
                      Monitoring Station: {planData.station_metadata.station} (
                      {planData.station_metadata.distance_km.toFixed(2)} km
                      away)
                    </div>
                  </div>
                </div>
              </div>

              {/* Hoisted AQI Hero + Data Confidence + Single Smog Episode Banner */}
              <ImpactJustification
                aqiData={planData.aqi_result}
                stationMetadata={planData.station_metadata}
                dataConfidence={planData.data_confidence}
                smogEpisodeActive={planData.smog_episode_active}
                variant="hero"
              />

              <p className="text-xs text-[var(--text-secondary)]">
                Exposure and transport results use illustrative breathing rates,
                infiltration, speeds and emission factors. These are scenario
                estimates, not personal health predictions.
              </p>
              {/* 3 Indian Household Preset Cards */}
              <HouseholdProfile
                selectedPresetId={selectedPreset?.id ?? null}
                onSelectPreset={onSelectPreset}
              />
            </div>
          )}

          {/* TAB 2: Routine & Commute */}
          {activeTab === 1 && (
            <div className="space-y-6">
              {onApplySchedule && (
                <ScheduleEditor
                  activities={activities}
                  onApply={onApplySchedule}
                  busy={updatingSchedule}
                />
              )}
              <TravelAdvice
                location={activeLocation}
                defaultDistance={
                  planData.commute_comparisons[0]?.distance_km ?? 12
                }
              />
              <p className="text-sm text-[var(--text-secondary)]">
                Car and two-wheeler figures use representative
                combustion-vehicle estimates.
                {planData.commute_comparisons.some(
                  (option) => option.mode === "metro",
                ) &&
                  " Metro operates in this urban area. Check whether it serves your trip."}
              </p>
              {/* Errand Consolidation Loop Card (if present) */}
              {errandsResult && (
                <div className="p-5 bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl shadow-xs space-y-4">
                  <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
                    <div className="flex items-center gap-2">
                      <span className="p-1 rounded-lg bg-teal-50 text-teal-700 dark:bg-teal-950 dark:text-teal-400">
                        <Route
                          className="w-4 h-4"
                          strokeWidth={1.75}
                          aria-hidden="true"
                        />
                      </span>
                      <h3 className="text-sm font-bold text-[var(--text-primary)]">
                        Errand Consolidation Loop (
                        {errandsResult.ordered_stops.length} Stops)
                      </h3>
                    </div>
                    <span className="px-3 py-1 text-xs font-bold rounded-full bg-teal-100 text-teal-900 dark:bg-teal-900/60 dark:text-teal-200 border border-teal-200 dark:border-teal-800 tabular-nums">
                      ↓ {errandsResult.pm25_dose_reduction_percent}% PM2.5
                      Inhalation Reduced
                    </span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <div className="p-3 bg-[var(--bg-elevated)] rounded-xl border border-[var(--border-subtle)]">
                      <div className="text-xs text-[var(--text-secondary)]">
                        Optimized Loop Distance
                      </div>
                      <div className="text-lg font-bold text-[var(--text-primary)] mt-0.5 font-mono tabular-nums">
                        {errandsResult.merged_loop_distance_km} km
                        <span className="text-xs text-teal-700 dark:text-teal-400 font-semibold ml-1">
                          (saved {errandsResult.distance_saved_km} km)
                        </span>
                      </div>
                    </div>

                    <div className="p-3 bg-[var(--bg-elevated)] rounded-xl border border-[var(--border-subtle)]">
                      <div className="text-xs text-[var(--text-secondary)]">
                        Tailpipe CO₂ Avoided
                      </div>
                      <div className="text-lg font-bold text-teal-700 dark:text-teal-400 mt-0.5 font-mono tabular-nums">
                        {errandsResult.tailpipe_co2_saved_grams} g
                      </div>
                    </div>

                    <div className="p-3 bg-[var(--bg-elevated)] rounded-xl border border-[var(--border-subtle)]">
                      <div className="text-xs text-[var(--text-secondary)]">
                        Clean-Air Time Window
                      </div>
                      <div className="text-lg font-bold text-teal-800 dark:text-teal-300 mt-0.5 font-mono tabular-nums">
                        {Math.floor(errandsResult.recommended_start_hour)}:00 –{" "}
                        {Math.floor(errandsResult.recommended_end_hour)}:30
                      </div>
                    </div>
                  </div>

                  <div>
                    <div className="text-xs font-semibold text-[var(--text-secondary)] mb-2">
                      Optimized Stop Sequence:
                    </div>
                    <ol className="flex flex-wrap items-center gap-2 text-xs">
                      {errandsResult.ordered_stops.map((stop, index) => (
                        <li key={stop.id} className="flex items-center gap-2">
                          <span className="px-3 py-1 bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-[var(--text-primary)] font-medium rounded-lg shadow-2xs">
                            {index + 1}. {stop.name} ({stop.duration_minutes}{" "}
                            min)
                          </span>
                          {index < errandsResult.ordered_stops.length - 1 && (
                            <Navigation
                              className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400 shrink-0 rotate-90"
                              aria-hidden="true"
                            />
                          )}
                        </li>
                      ))}
                    </ol>
                  </div>

                  <MathDrawer title="Show the Math: Errand Permutation & Tailpipe CO₂ Factors">
                    <p>
                      <strong>Brute-Force Permutations:</strong> Evaluates all{" "}
                      {errandsResult.ordered_stops.length}! = 24 travel routes
                      respecting fixed opening/closing shop windows and school
                      dismissal.
                    </p>
                    <code className="block bg-[var(--bg-surface)] p-2 rounded border border-[var(--border-subtle)] font-mono tabular-nums text-[var(--text-primary)]">
                      CO₂ Saved = Total Separate Trip Distance (
                      {errandsResult.distance_saved_km} km) × Tailpipe Factor
                      (160 g/km auto-rickshaw/hatchback)
                    </code>
                  </MathDrawer>
                </div>
              )}

              {/* Diurnal Schedule & Commute Matrix (Smog banner deduplicated in Tab 1, Briefings in Tab 4) */}
              <p className="text-sm text-[var(--text-secondary)]">
                {planData.history_source}
              </p>
              <LowEmissionRoutine
                commuteOptions={planData.commute_comparisons}
                routineResult={planData.routine_optimization}
                whatsappCard={planData.whatsapp_card}
                communityBrief={planData.community_brief}
                smogEpisodeActive={false}
                hideSmogAlert={true}
                hideBriefings={true}
              />
            </div>
          )}

          {/* TAB 3: Indoor Air & CADR */}
          {activeTab === 2 && (
            <IndoorAirGuide
              initialGuidance={cadrGuidance}
              initialDimensions={selectedPreset?.room_dimensions}
              initialFactors={selectedPreset?.indoor_factors}
              onRecalculate={onRecalculateCADR}
            />
          )}

          {/* TAB 4: Briefings & Impact */}
          {activeTab === 3 && (
            <div className="space-y-6">
              {/* Copy-Ready Briefings: WhatsApp Family Card & RWA School Brief tabs */}
              <div className="p-5 sm:p-6 bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl shadow-xs space-y-4">
                <div className="flex items-center gap-2">
                  <span className="p-1.5 rounded-lg bg-teal-50 text-teal-700 dark:bg-teal-950 dark:text-teal-400">
                    <FileText
                      className="w-4 h-4"
                      strokeWidth={1.75}
                      aria-hidden="true"
                    />
                  </span>
                  <div>
                    <h2 className="text-base sm:text-lg font-bold text-[var(--text-primary)]">
                      4. Actionable Briefings & Community Advisories
                    </h2>
                    <p className="text-xs text-[var(--text-secondary)] mt-0.5">
                      Copy-ready personalized WhatsApp briefings and RWA/school
                      action advisories.
                    </p>
                  </div>
                </div>
                <BriefingCards
                  whatsappCard={planData.whatsapp_card}
                  communityBrief={planData.community_brief}
                />
              </div>

              {/* Show the Math Drawers (CPCB linear formula, Berkeley Earth, WHO/NAAQS) */}
              <ImpactJustification
                aqiData={planData.aqi_result}
                stationMetadata={planData.station_metadata}
                dataConfidence={planData.data_confidence}
                errandsResult={null}
                variant="details"
              />
            </div>
          )}
          <RecommendationCards
            cards={(planData.recommendation_cards ?? []).filter(
              (card) =>
                activeTab === 0 ||
                (activeTab === 1 && card.pillar === "routine") ||
                (activeTab === 2 && card.pillar === "indoor") ||
                (activeTab === 3 && card.pillar === "impact"),
            )}
          />
        </m.div>
      </AnimatePresence>
    </div>
  );
};

export default DashboardShell;
