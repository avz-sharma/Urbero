import { formatHour } from "./ScheduleEditor";
import React, { lazy, Suspense, useState } from "react";
import { m, AnimatePresence } from "motion/react";
import {
  CalendarClock,
  AlertOctagon,
  Sparkles,
  BarChart2,
  Table as TableIcon,
  MessageSquare,
  Building2,
} from "lucide-react";
import type {
  CommunityBrief,
  CommuteModeComparison,
  RoutineOptimizationResult,
  WhatsAppFamilyCard,
} from "../api/types";
import { CopyButton } from "../common/CopyButton";
import { snappySpring } from "../lib/motion";
import { getModeIcon } from "./commuteIcons";

const CommuteBars = lazy(() => import("./CommuteBars"));

export interface BriefingCardsProps {
  whatsappCard: WhatsAppFamilyCard;
  communityBrief: CommunityBrief;
}

export const BriefingCards: React.FC<BriefingCardsProps> = ({
  whatsappCard,
  communityBrief,
}) => {
  const [activeTab, setActiveTab] = useState<"whatsapp" | "community">(
    "whatsapp",
  );

  return (
    <div className="border border-teal-200 dark:border-teal-800 bg-teal-50/30 dark:bg-teal-950/20 rounded-xl p-4 space-y-3">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
        <div
          className="relative flex items-center p-1 bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl"
          role="group"
          aria-label="Briefing Format Selector"
        >
          <button
            type="button"
            onClick={() => setActiveTab("whatsapp")}
            aria-pressed={activeTab === "whatsapp"}
            className={`relative z-10 min-h-[44px] px-3.5 py-1.5 text-xs font-bold rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-teal-500 inline-flex items-center gap-1.5 cursor-pointer ${
              activeTab === "whatsapp"
                ? "text-teal-900 dark:text-teal-100"
                : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
            }`}
          >
            {activeTab === "whatsapp" && (
              <m.div
                layoutId="briefing-tab"
                transition={snappySpring}
                className="absolute inset-0 bg-teal-100 dark:bg-teal-900/60 rounded-lg -z-10 border border-teal-300 dark:border-teal-700"
              />
            )}
            <MessageSquare
              className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400"
              strokeWidth={1.75}
              aria-hidden="true"
            />
            <span>WhatsApp Family Card</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("community")}
            aria-pressed={activeTab === "community"}
            className={`relative z-10 min-h-[44px] px-3.5 py-1.5 text-xs font-bold rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-teal-500 inline-flex items-center gap-1.5 cursor-pointer ${
              activeTab === "community"
                ? "text-teal-900 dark:text-teal-100"
                : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
            }`}
          >
            {activeTab === "community" && (
              <m.div
                layoutId="briefing-tab"
                transition={snappySpring}
                className="absolute inset-0 bg-teal-100 dark:bg-teal-900/60 rounded-lg -z-10 border border-teal-300 dark:border-teal-700"
              />
            )}
            <Building2
              className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400"
              strokeWidth={1.75}
              aria-hidden="true"
            />
            <span>RWA & School Brief</span>
          </button>
        </div>

        <CopyButton
          textToCopy={
            activeTab === "whatsapp"
              ? whatsappCard.formatted_message
              : communityBrief.formatted_brief
          }
          defaultLabel={
            activeTab === "whatsapp"
              ? "📋 Copy WhatsApp Card"
              : "📋 Copy Community Brief"
          }
        />
      </div>

      <pre
        tabIndex={0}
        className="whitespace-pre-wrap font-sans text-xs bg-[var(--bg-surface)] p-3.5 rounded-xl border border-[var(--border-subtle)] text-[var(--text-primary)] leading-relaxed overflow-x-auto max-h-64 focus:outline-none focus:ring-2 focus:ring-teal-500 shadow-2xs"
      >
        {activeTab === "whatsapp"
          ? whatsappCard.formatted_message
          : communityBrief.formatted_brief}
      </pre>
    </div>
  );
};

export interface LowEmissionRoutineProps {
  commuteOptions: CommuteModeComparison[];
  routineResult: RoutineOptimizationResult;
  whatsappCard?: WhatsAppFamilyCard;
  communityBrief?: CommunityBrief;
  smogEpisodeActive: boolean;
  hideSmogAlert?: boolean;
  hideBriefings?: boolean;
}

export const LowEmissionRoutine: React.FC<LowEmissionRoutineProps> = ({
  commuteOptions,
  routineResult,
  whatsappCard,
  communityBrief,
  smogEpisodeActive,
  hideSmogAlert = false,
  hideBriefings = false,
}) => {
  const [commuteView, setCommuteView] = useState<"table" | "visual">("table");

  // Calculate max values for proportional bar scaling

  return (
    <section
      aria-labelledby="low-emission-pillar-heading"
      className="bg-[var(--bg-surface)] p-5 sm:p-6 rounded-2xl border border-[var(--border-subtle)] shadow-xs space-y-6 transition-colors"
    >
      <div>
        <div className="flex items-center gap-2">
          <span className="p-1.5 rounded-lg bg-teal-50 text-teal-700 dark:bg-teal-950 dark:text-teal-400">
            <CalendarClock
              className="w-4 h-4"
              strokeWidth={1.75}
              aria-hidden="true"
            />
          </span>
          <h2
            id="low-emission-pillar-heading"
            className="text-lg sm:text-xl font-bold text-[var(--text-primary)]"
          >
            2. Low-Emission Daily Routine & Commute
          </h2>
        </div>
        <p className="text-xs text-[var(--text-secondary)] mt-1">
          Safer travel modes, diurnal routine re-alignment, and WhatsApp/RWA
          community briefings.
        </p>
      </div>

      {smogEpisodeActive && !hideSmogAlert && (
        <AnimatePresence initial={false}>
          <m.div
            role="alert"
            aria-live="assertive"
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            className="p-4 rounded-xl bg-[#FEF2F2] text-[#991B1B] border-l-4 border-[#DC2626] dark:bg-[#310B0E] dark:text-[#FECACA] dark:border-l-4 dark:border-[#F87171] space-y-2 shadow-2xs"
          >
            <div className="flex items-center gap-2 font-black text-sm text-[#991B1B] dark:text-[#FECACA]">
              <AlertOctagon
                className="w-4 h-4 text-[#DC2626] dark:text-[#F87171] shrink-0"
                strokeWidth={2}
                aria-hidden="true"
              />
              <span>SMOG EPISODE ACTIVE — VERY POOR / SEVERE AIR QUALITY</span>
            </div>
            <p className="text-xs leading-relaxed text-[#991B1B] dark:text-[#FECACA]">
              Sensitive individuals (asthmatics, seniors, and young children)
              should strictly avoid outdoor morning workouts and outdoor recess.
              If outdoor travel is mandatory, wear a{" "}
              <strong>fitted N95/FFP2 respirator mask</strong> (cloth and
              surgical masks provide zero seal and do not block PM2.5
              particulates). Consult a doctor or healthcare professional for
              individualized medical action plans.
            </p>
          </m.div>
        </AnimatePresence>
      )}

      {/* Routine Optimization Before vs After */}
      {routineResult.activities.length > 0 && (
        <div className="border border-[var(--border-subtle)] rounded-xl p-4 bg-[var(--bg-elevated)] space-y-3">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
            <h3 className="text-sm font-bold text-[var(--text-primary)]">
              Diurnal Household Schedule Optimization
            </h3>
            <span className="inline-flex items-center gap-1 px-3 py-1 text-xs font-bold rounded-full bg-teal-100 text-teal-900 dark:bg-teal-900/60 dark:text-teal-200 border border-teal-200 dark:border-teal-800 tabular-nums">
              <Sparkles
                className="w-3.5 h-3.5 text-teal-700 dark:text-teal-300"
                strokeWidth={1.75}
                aria-hidden="true"
              />
              ↓ {routineResult.total_dose_reduction_percent}% Inhaled PM2.5
              Reduced ({routineResult.total_dose_reduction_ug} µg)
            </span>
          </div>

          <p className="text-xs text-[var(--text-secondary)]">
            {routineResult.overall_advisory}
          </p>

          <div className="overflow-x-auto rounded-lg border border-[var(--border-subtle)]">
            <table className="w-full text-left text-xs border-collapse">
              <caption className="sr-only">
                Household member activities before and after diurnal
                optimization
              </caption>
              <thead className="bg-[var(--bg-canvas)] text-[var(--text-secondary)]">
                <tr>
                  <th
                    scope="col"
                    className="p-2.5 border-b border-[var(--border-subtle)] font-semibold"
                  >
                    Activity & Member
                  </th>
                  <th
                    scope="col"
                    className="p-2.5 border-b border-[var(--border-subtle)] font-semibold"
                  >
                    Original Time
                  </th>
                  <th
                    scope="col"
                    className="p-2.5 border-b border-[var(--border-subtle)] font-semibold"
                  >
                    Optimized Slot
                  </th>
                  <th
                    scope="col"
                    className="p-2.5 border-b border-[var(--border-subtle)] font-semibold"
                  >
                    Dose Saved
                  </th>
                  <th
                    scope="col"
                    className="p-2.5 border-b border-[var(--border-subtle)] font-semibold"
                  >
                    Advisory Action
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border-subtle)] bg-[var(--bg-surface)]">
                {routineResult.activities.map((act) => (
                  <tr
                    key={act.activity_id}
                    className="hover:bg-[var(--bg-elevated)] transition-colors"
                  >
                    <td className="p-2.5 font-medium text-[var(--text-primary)]">
                      <div>{act.activity_name}</div>
                      <div className="text-[11px] text-[var(--text-secondary)]">
                        {act.member_name}
                      </div>
                    </td>
                    <td className="p-2.5 text-[var(--text-secondary)] font-mono tabular-nums">
                      {formatHour(act.original_start_hour)} –{" "}
                      {formatHour(act.original_end_hour)}
                    </td>
                    <td className="p-2.5 font-semibold text-teal-700 dark:text-teal-400 font-mono tabular-nums">
                      {formatHour(act.optimized_start_hour)} –{" "}
                      {formatHour(act.optimized_end_hour)}
                      {act.is_shifted_indoors && (
                        <span className="block text-[10px] text-purple-700 dark:text-purple-400 font-normal">
                          Shifted Indoors (HEPA)
                        </span>
                      )}
                    </td>
                    <td className="p-2.5 text-teal-700 dark:text-teal-400 font-bold font-mono tabular-nums">
                      {act.dose_reduction_ug > 0
                        ? `-${act.dose_reduction_ug} µg`
                        : "Baseline"}
                    </td>
                    <td className="p-2.5 text-[var(--text-secondary)] text-[11px] max-w-xs">
                      {act.recommendation_note}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Planet vs. Lungs Commute Comparison (Theme-Corrected: Optimal Win-Win bg-[#ECFDF5]/85 text-[#0F1B1D] dark:bg-[#052E24]/60 dark:text-[#F0F5F4], Planet vs Lungs Conflict bg-[#FEF2F2]/85 text-[#0F1B1D] dark:bg-[#310B0E]/60 dark:text-[#F0F5F4]) */}
      <div className="border border-[var(--border-subtle)] rounded-xl p-4 bg-[var(--bg-elevated)] space-y-3">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
          <div>
            <h3 className="text-sm font-bold text-[var(--text-primary)]">
              Planet vs. Lungs: Commute Mode Trade-off
            </h3>
            <p className="text-xs text-[var(--text-secondary)] mt-0.5">
              Highlights the critical tension: zero-emission cycling eliminates
              CO2 but drastically multiplies lung exposure during severe smog.
            </p>
          </div>

          {/* Accessible Table / Visual Bars View Toggle */}
          <div
            className="flex items-center gap-1 bg-[var(--bg-surface)] p-1 rounded-lg border border-[var(--border-subtle)] shrink-0"
            role="group"
            aria-label="Commute Matrix View"
          >
            <button
              type="button"
              onClick={() => setCommuteView("table")}
              aria-pressed={commuteView === "table"}
              className={`min-h-[44px] px-2.5 py-1 text-xs font-semibold rounded-md transition-colors inline-flex items-center gap-1.5 focus:outline-none focus:ring-2 focus:ring-teal-500 cursor-pointer ${
                commuteView === "table"
                  ? "bg-teal-700 text-white dark:bg-teal-600"
                  : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
              }`}
            >
              <TableIcon
                className="w-3.5 h-3.5"
                strokeWidth={1.75}
                aria-hidden="true"
              />
              <span>Table</span>
            </button>
            <button
              type="button"
              onClick={() => setCommuteView("visual")}
              aria-pressed={commuteView === "visual"}
              className={`min-h-[44px] px-2.5 py-1 text-xs font-semibold rounded-md transition-colors inline-flex items-center gap-1.5 focus:outline-none focus:ring-2 focus:ring-teal-500 cursor-pointer ${
                commuteView === "visual"
                  ? "bg-teal-700 text-white dark:bg-teal-600"
                  : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
              }`}
            >
              <BarChart2
                className="w-3.5 h-3.5"
                strokeWidth={1.75}
                aria-hidden="true"
              />
              <span>Visual Bars</span>
            </button>
          </div>
        </div>

        {/* Semantic HTML Table View (Always available for screen readers & table tab) */}
        <div
          className={`overflow-x-auto rounded-lg border border-[var(--border-subtle)] ${commuteView === "visual" ? "sr-only" : "block"}`}
        >
          <table className="w-full text-left text-xs border-collapse">
            <caption className="sr-only">
              Side-by-side commute mode comparison of personal inhaled PM2.5 and
              transport CO2 (tailpipe/grid)
            </caption>
            <thead className="bg-[var(--bg-canvas)] text-[var(--text-secondary)]">
              <tr>
                <th
                  scope="col"
                  className="p-2.5 border-b border-[var(--border-subtle)] font-semibold"
                >
                  Commute Mode
                </th>
                <th
                  scope="col"
                  className="p-2.5 border-b border-[var(--border-subtle)] font-semibold"
                >
                  Transport CO₂ (g)
                </th>
                <th
                  scope="col"
                  className="p-2.5 border-b border-[var(--border-subtle)] font-semibold"
                >
                  Inhaled PM₂.₅ (µg)
                </th>
                <th
                  scope="col"
                  className="p-2.5 border-b border-[var(--border-subtle)] font-semibold"
                >
                  Duration
                </th>
                <th
                  scope="col"
                  className="p-2.5 border-b border-[var(--border-subtle)] font-semibold"
                >
                  Trade-off Insight
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border-subtle)] bg-[var(--bg-surface)]">
              {commuteOptions.map((c) => {
                const isOptimal =
                  c.mode.toLowerCase() === "metro" ||
                  c.planet_vs_lungs_note.toLowerCase().includes("win-win");
                const isConflict =
                  c.planet_vs_lungs_note.toLowerCase().includes("hazard") ||
                  c.planet_vs_lungs_note.toLowerCase().includes("conflict");
                const ModeIcon = getModeIcon(c.mode);

                return (
                  <tr
                    key={c.mode}
                    className={`transition-colors ${
                      isOptimal
                        ? "bg-[#ECFDF5]/85 text-[#0F1B1D] dark:bg-[#052E24]/60 dark:text-[#F0F5F4] hover:bg-teal-100/50 dark:hover:bg-teal-950/40"
                        : isConflict
                          ? "bg-[#FEF2F2]/85 text-[#0F1B1D] dark:bg-[#310B0E]/60 dark:text-[#F0F5F4] hover:bg-amber-100/40 dark:hover:bg-amber-950/30"
                          : "hover:bg-[var(--bg-elevated)]"
                    }`}
                  >
                    <td className="p-2.5 font-semibold text-[var(--text-primary)]">
                      <div className="flex items-center gap-1.5">
                        <ModeIcon
                          className="w-4 h-4 text-teal-600 dark:text-teal-400 shrink-0"
                          strokeWidth={1.75}
                          aria-hidden="true"
                        />
                        <span>{c.label}</span>
                      </div>
                      {isOptimal && (
                        <span className="inline-block mt-0.5 text-[10px] font-bold px-1.5 py-0.2 rounded bg-teal-200 dark:bg-teal-800 text-teal-900 dark:text-teal-100">
                          Optimal Win-Win
                        </span>
                      )}
                      {isConflict && (
                        <span className="inline-block mt-0.5 text-[10px] font-bold px-1.5 py-0.2 rounded bg-amber-200 dark:bg-amber-900 text-amber-900 dark:text-amber-100">
                          Planet vs. Lungs Conflict
                        </span>
                      )}
                    </td>
                    <td className="p-2.5 font-mono tabular-nums text-[var(--text-secondary)]">
                      {c.tailpipe_co2_grams} g
                    </td>
                    <td className="p-2.5 font-mono tabular-nums font-bold text-[var(--text-primary)]">
                      {c.personal_inhaled_pm25_ug} µg
                    </td>
                    <td className="p-2.5 text-[var(--text-secondary)] font-mono tabular-nums">
                      {c.duration_minutes} min
                    </td>
                    <td className="p-2.5 text-[var(--text-secondary)] text-[11px] max-w-sm">
                      {c.planet_vs_lungs_note}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {commuteView === "visual" && (
          <Suspense fallback={<p role="status">Loading commute bars…</p>}>
            <CommuteBars commuteOptions={commuteOptions} />
          </Suspense>
        )}
      </div>

      {/* Copy-Ready Briefings */}
      {!hideBriefings && whatsappCard && communityBrief && (
        <BriefingCards
          whatsappCard={whatsappCard}
          communityBrief={communityBrief}
        />
      )}
    </section>
  );
};
