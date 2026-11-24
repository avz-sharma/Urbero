import React from "react";
import { m, AnimatePresence } from "motion/react";
import {
  MapPin,
  Clock,
  Navigation,
  Route,
  Leaf,
  AlertOctagon,
} from "lucide-react";
import type {
  ConfidenceResult,
  CPCBAQIResult,
  MergedErrandsResult,
  StationMetadataSchema,
} from "../api/types";
import { ConfidenceBadge } from "../common/ConfidenceBadge";
import { MathDrawer } from "../common/MathDrawer";
import { getAQIBand } from "../lib/aqiTheme";

export interface ImpactJustificationProps {
  aqiData: CPCBAQIResult;
  stationMetadata: StationMetadataSchema;
  dataConfidence: ConfidenceResult;
  errandsResult?: MergedErrandsResult | null;
  variant?: "all" | "hero" | "details";
  smogEpisodeActive?: boolean;
}

export const ImpactJustification: React.FC<ImpactJustificationProps> = ({
  aqiData,
  stationMetadata,
  dataConfidence,
  errandsResult,
  variant = "all",
  smogEpisodeActive = false,
}) => {
  const subIndices = aqiData.sub_indices || [];
  const overallBand = getAQIBand(aqiData.overall_aqi);
  const AQIIcon = overallBand.icon;

  const showHero = variant === "all" || variant === "hero";
  const showDetails = variant === "all" || variant === "details";

  const isSevereSmog =
    smogEpisodeActive ||
    aqiData.category.toLowerCase().includes("very poor") ||
    aqiData.category.toLowerCase().includes("severe");

  const sectionLabelId =
    variant === "hero"
      ? "aqi-command-hero-heading"
      : "impact-justification-title";

  return (
    <section
      aria-labelledby={sectionLabelId}
      className="space-y-6"
    >
      {!aqiData.is_valid && <p className="text-sm">{aqiData.validation_message} Available particulate sub-indices remain estimates; no overall CPCB AQI is published.</p>}
      <p className="text-xs text-[var(--text-secondary)]">{stationMetadata.conversion_note}</p>
      {/* Hidden heading for hero variant to satisfy landmark-unique */}
      {variant === "hero" && (
        <h2 id="aqi-command-hero-heading" className="sr-only">
          Air Quality Index Command Center
        </h2>
      )}

      {/* Title for full view or details view */}
      {showDetails && (
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-teal-50 text-teal-700 dark:bg-teal-950 dark:text-teal-400">
              <Leaf className="w-4 h-4" strokeWidth={1.75} aria-hidden="true" />
            </span>
            <h2 id="impact-justification-title" className="text-lg sm:text-xl font-bold text-[var(--text-primary)]">
              4. Sustainable Alternatives & Impact Justification
            </h2>
          </div>
          <p className="text-xs text-[var(--text-secondary)] mt-1">
            CPCB National AQI verification, Data Confidence scoring, and quantified errand consolidation.
          </p>
        </div>
      )}

      {/* Above-the-Fold AQI Command Hero */}
      {showHero && (
        <div
          data-testid="aqi-command-hero"
          className="grid grid-cols-1 lg:grid-cols-12 gap-5"
        >
          {/* Left Column (7 cols): CPCB National AQI Card (Theme-Corrected: Light bg-[#FEF2F2]/95, Dark dark:bg-[#310B0E]/90) */}
          <div
            className="lg:col-span-7 p-5 sm:p-6 rounded-2xl border-2 transition-all shadow-xs flex flex-col justify-between bg-[#FEF2F2]/95 text-[#991B1B] border-[#FCA5A5] dark:bg-[#310B0E]/90 dark:text-[#FCA5A5] dark:border-[#991B1B]"
          >
            <div>
              {/* Header Strip */}
              <div className="flex justify-between items-center flex-wrap gap-2 mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-black uppercase tracking-wider text-gray-800 dark:text-gray-200">
                    CPCB breakpoint estimate
                  </span>
                  <span
                    className={`inline-flex items-center gap-1 px-2.5 py-0.5 text-[11px] font-bold rounded-full border ${
                      stationMetadata.status === "live"
                        ? "bg-emerald-100 text-emerald-800 border-emerald-300 dark:bg-emerald-950 dark:text-emerald-300 dark:border-emerald-700"
                        : "bg-amber-100 text-amber-800 border-amber-300 dark:bg-amber-950 dark:text-amber-300 dark:border-amber-700"
                    }`}
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-current" aria-hidden="true" />
                    ● {stationMetadata.status === "modelled_live" ? "MODELLED CURRENT" : stationMetadata.status.toUpperCase()}
                  </span>
                </div>

                <div className="text-[11px] font-medium text-gray-600 dark:text-gray-300 flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5" strokeWidth={1.75} aria-hidden="true" />
                  <span>
                    Observed: {new Date(stationMetadata.observed_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </span>
                </div>
              </div>

              {/* AQI Tabular Score & Category Pill */}
              <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-4 py-2">
                <div className="flex items-baseline gap-3">
                  <div
                    className="text-5xl sm:text-6xl font-black tracking-tight font-mono tabular-nums text-[#991B1B] dark:text-[#FCA5A5]"
                  >
                    {aqiData.is_valid ? aqiData.overall_aqi : "—"}
                  </div>
                  <div>
                    <div
                      className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-black border shadow-2xs bg-white text-[#991B1B] border-[#FCA5A5] dark:bg-[#121B20] dark:text-[#FCA5A5] dark:border-[#991B1B]"
                    >
                      <AQIIcon className="w-4 h-4" strokeWidth={2} aria-hidden="true" />
                      <span>{aqiData.is_valid ? aqiData.category : "Insufficient pollutants"}</span>
                    </div>
                    <div className="text-xs text-gray-700 dark:text-gray-300 mt-1">
                      Dominant parameter: <span className="font-bold text-gray-900 dark:text-white">{aqiData.dominant_pollutant}</span>
                    </div>
                  </div>
                </div>

                <div className="text-xs text-gray-700 dark:text-gray-300 space-y-0.5 sm:text-right">
                  <div className="font-semibold text-gray-900 dark:text-white">
                    {stationMetadata.station}
                  </div>
                  <div>
                    {stationMetadata.distance_km.toFixed(2)} km away · {stationMetadata.source}
                  </div>
                </div>
              </div>
            </div>

            {/* Compact Measured Pollutant Sub-Indices Strip (Theme-Corrected: Light bg-white text-[#0F1B1D], Dark dark:bg-[#19252C] dark:text-[#F0F5F4]) */}
            <div className="mt-4 pt-4 border-t border-gray-300/60 dark:border-gray-700/60">
              <div className="text-xs font-bold text-gray-800 dark:text-gray-200 mb-2.5">
                Available Pollutant Sub-Indices:
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2.5">
                {subIndices.map((sub) => {
                  const subBand = getAQIBand(sub.category);
                  const progressWidth = Math.min(Math.round((sub.sub_index / 500) * 100), 100);

                  return (
                    <div
                      key={sub.pollutant}
                      className="p-2.5 rounded-xl bg-white text-[#0F1B1D] border border-[#DCE4E1] dark:bg-[#19252C] dark:text-[#F0F5F4] dark:border-[#24343D] shadow-2xs space-y-1"
                    >
                      <div className="flex justify-between items-center text-xs">
                        <span className="font-bold text-[#0F1B1D] dark:text-[#F0F5F4]">{sub.pollutant}</span>
                        <span className="font-mono tabular-nums text-[11px] text-gray-600 dark:text-gray-300">
                          {sub.concentration} {sub.unit}
                        </span>
                      </div>

                      <div className="flex justify-between items-baseline pt-0.5">
                        <span
                          className="text-base font-black font-mono tabular-nums"
                          style={{ color: subBand.light.text }}
                        >
                          {sub.sub_index}
                        </span>
                        <span className="text-[10px] font-semibold text-gray-500 dark:text-gray-400">
                          {sub.category}
                        </span>
                      </div>

                      {/* Sub-index Progress Bar */}
                      <div className="w-full h-1.5 bg-gray-200 dark:bg-gray-800 rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all duration-300"
                          style={{
                            width: `${progressWidth}%`,
                            backgroundColor: subBand.light.text,
                          }}
                          aria-hidden="true"
                        />
                      </div>
                    </div>
                  );
                })}
              </div>

              <p className="text-[11px] text-gray-600 dark:text-gray-400 mt-2.5 italic">
                {aqiData.validation_message}
              </p>
            </div>
          </div>

          {/* Right Column (5 cols): Trust & Smog Alert Stack */}
          <div className="lg:col-span-5 flex flex-col justify-between gap-4">
            {/* Data Confidence Card */}
            <div className="p-4 sm:p-5 rounded-2xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] shadow-xs space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-xs font-bold text-[var(--text-secondary)] uppercase tracking-wide">
                  Provenance & Trust
                </span>
                <ConfidenceBadge confidence={dataConfidence} />
              </div>
              <p className="text-xs text-[var(--text-primary)] leading-relaxed">
                {dataConfidence.reason}
              </p>
              <div className="pt-2 border-t border-[var(--border-subtle)] flex items-center justify-between text-[11px] text-[var(--text-secondary)]">
                <span className="flex items-center gap-1">
                  <MapPin className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" strokeWidth={1.75} aria-hidden="true" />
                  Station Source: {stationMetadata.source}
                </span>
                <span className="font-mono tabular-nums">{stationMetadata.distance_km.toFixed(2)} km</span>
              </div>
            </div>

            {/* Conditional Smog Episode Mode Alert Banner (Theme-Corrected: Light bg-[#FEF2F2], Dark dark:bg-[#310B0E]) */}
            <AnimatePresence initial={false}>
              {isSevereSmog && (
                <m.div
                  role="alert"
                  aria-live="assertive"
                  initial={{ opacity: 0, y: -6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -6 }}
                  className="p-4 sm:p-5 rounded-2xl bg-[#FEF2F2] text-[#991B1B] border-l-4 border-[#DC2626] dark:bg-[#310B0E] dark:text-[#FECACA] dark:border-l-4 dark:border-[#F87171] shadow-xs space-y-2"
                >
                  <div className="flex items-center gap-2 font-black text-sm text-[#991B1B] dark:text-[#FECACA]">
                    <AlertOctagon className="w-4 h-4 text-[#DC2626] dark:text-[#F87171] shrink-0" strokeWidth={2} aria-hidden="true" />
                    <span>SMOG EPISODE ACTIVE — VERY POOR / SEVERE AIR QUALITY</span>
                  </div>
                  <p className="text-xs leading-relaxed text-[#991B1B] dark:text-[#FECACA]">
                    Sensitive individuals (asthmatics, seniors, and young children) should strictly avoid outdoor morning workouts and outdoor recess.
                    If outdoor travel is mandatory, wear a <strong>fitted N95/FFP2 respirator mask</strong> (cloth and surgical masks provide zero seal and do not block PM2.5 particulates).
                    Consult a doctor or healthcare professional for individualized medical action plans.
                  </p>
                </m.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      )}

      {/* Sustainable Alternatives: Errand Consolidation Loop & Math Drawers */}
      {showDetails && (
        <div className="space-y-4">
          {errandsResult && (
            <div className="p-5 bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl shadow-xs space-y-4">
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
                <div className="flex items-center gap-2">
                  <span className="p-1 rounded-lg bg-teal-50 text-teal-700 dark:bg-teal-950 dark:text-teal-400">
                    <Route className="w-4 h-4" strokeWidth={1.75} aria-hidden="true" />
                  </span>
                  <h3 className="text-sm font-bold text-[var(--text-primary)]">
                    Errand Consolidation Loop ({errandsResult.ordered_stops.length} Stops)
                  </h3>
                </div>
                <span className="px-3 py-1 text-xs font-bold rounded-full bg-teal-100 text-teal-900 dark:bg-teal-900/60 dark:text-teal-200 border border-teal-200 dark:border-teal-800 tabular-nums">
                  ↓ {errandsResult.pm25_dose_reduction_percent}% PM2.5 Inhalation Reduced
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="p-3 bg-[var(--bg-elevated)] rounded-xl border border-[var(--border-subtle)]">
                  <div className="text-xs text-[var(--text-secondary)]">Optimized Loop Distance</div>
                  <div className="text-lg font-bold text-[var(--text-primary)] mt-0.5 font-mono tabular-nums">
                    {errandsResult.merged_loop_distance_km} km
                    <span className="text-xs text-teal-700 dark:text-teal-400 font-semibold ml-1">
                      (saved {errandsResult.distance_saved_km} km)
                    </span>
                  </div>
                </div>

                <div className="p-3 bg-[var(--bg-elevated)] rounded-xl border border-[var(--border-subtle)]">
                  <div className="text-xs text-[var(--text-secondary)]">Tailpipe CO₂ Avoided</div>
                  <div className="text-lg font-bold text-teal-700 dark:text-teal-400 mt-0.5 font-mono tabular-nums">
                    {errandsResult.tailpipe_co2_saved_grams} g
                  </div>
                </div>

                <div className="p-3 bg-[var(--bg-elevated)] rounded-xl border border-[var(--border-subtle)]">
                  <div className="text-xs text-[var(--text-secondary)]">Clean-Air Time Window</div>
                  <div className="text-lg font-bold text-teal-800 dark:text-teal-300 mt-0.5 font-mono tabular-nums">
                    {Math.floor(errandsResult.recommended_start_hour)}:00 – {Math.floor(errandsResult.recommended_end_hour)}:30
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
                        {index + 1}. {stop.name} ({stop.duration_minutes} min)
                      </span>
                      {index < errandsResult.ordered_stops.length - 1 && (
                        <Navigation className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400 shrink-0 rotate-90" aria-hidden="true" />
                      )}
                    </li>
                  ))}
                </ol>
              </div>

              <MathDrawer title="Show the Math: Errand Permutation & Tailpipe CO₂ Factors">
                <p>
                  <strong>Brute-Force Permutations:</strong> Evaluates all {errandsResult.ordered_stops.length}! = 24 travel routes respecting fixed opening/closing shop windows and school dismissal.
                </p>
                <code className="block bg-[var(--bg-surface)] p-2 rounded border border-[var(--border-subtle)] font-mono tabular-nums text-[var(--text-primary)]">
                  CO₂ Saved = Total Separate Trip Distance ({errandsResult.distance_saved_km} km) × Tailpipe Factor (160 g/km auto-rickshaw/hatchback)
                </code>
              </MathDrawer>
            </div>
          )}

          {/* Expandable Show the Math Drawer for CPCB AQI & Dose */}
          <MathDrawer title="Show the Math: CPCB Linear Breakpoint Formula & Exposure Baselines">
            <div>
              <strong className="text-[var(--text-primary)]">1. CPCB Sub-Index Linear Interpolation:</strong>
              <code className="block bg-[var(--bg-surface)] p-2 rounded border border-[var(--border-subtle)] font-mono tabular-nums mt-1 text-[var(--text-primary)]">
                Ip = [ (I_Hi - I_Lo) / (BP_Hi - BP_Lo) ] × (Cp - BP_Lo) + I_Lo
              </code>
              <p className="text-[11px] text-[var(--text-secondary)] mt-1">
                Where Cp is the pollutant concentration, [BP_Lo, BP_Hi] is the Indian NAAQS breakpoint interval, and [I_Lo, I_Hi] is the corresponding AQI category interval.
              </p>
            </div>

            <div>
              <strong className="text-[var(--text-primary)]">2. Inhaled Particulate Dose Equation:</strong>
              <code className="block bg-[var(--bg-surface)] p-2 rounded border border-[var(--border-subtle)] font-mono tabular-nums mt-1 text-[var(--text-primary)]">
                Dose (µg) = Concentration (µg/m³) × Breathing Rate (m³/h) × Duration (h) × Infiltration Multiplier
              </code>
            </div>

            {/* Mandatory Honesty Labels */}
            <div className="p-3.5 bg-amber-50 dark:bg-amber-950/20 border border-amber-300 dark:border-amber-800 rounded-xl text-amber-950 dark:text-amber-200 space-y-2">
              <div>
                <strong>🚬 Berkeley Earth Cigarette Heuristic:</strong>
                <p className="mt-0.5 text-[11px] leading-relaxed">
                  ~22 µg/m³ of PM2.5 over a 24-hour duration is roughly equivalent to smoking 1 cigarette in terms of inhaled mass.
                  <em className="block font-semibold mt-0.5 text-amber-900 dark:text-amber-300">
                    Mandatory Label: This is a public communication heuristic for intuitive risk comparison, NOT a clinical equivalence or diagnostic measure.
                  </em>
                </p>
              </div>

              <div className="pt-2 border-t border-amber-200 dark:border-amber-800">
                <strong>🏛️ Regulatory Reference Baselines:</strong>
                <p className="mt-0.5 text-[11px] leading-relaxed">
                  WHO 2021 24-hour guideline: 15 µg/m³ · India NAAQS 24-hour limit: 60 µg/m³.
                  <em className="block font-semibold mt-0.5 text-amber-900 dark:text-amber-300">
                    Mandatory Label: These are population-level regulatory safety baselines, NEVER a "personal safe budget" for toxic particulate inhalation.
                  </em>
                </p>
              </div>
            </div>
          </MathDrawer>
        </div>
      )}
    </section>
  );
};
