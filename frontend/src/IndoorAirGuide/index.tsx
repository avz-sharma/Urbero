import React, { useState } from "react";
import { Wind, ShieldAlert, CheckCircle2, AlertTriangle, Sparkles } from "lucide-react";
import type { RoomCADRResult, RoomDimensions, RoomIndoorFactors } from "../api/types";
import { MathDrawer } from "../common/MathDrawer";

export interface IndoorAirGuideProps {
  initialGuidance: RoomCADRResult;
  initialDimensions?: RoomDimensions;
  initialFactors?: RoomIndoorFactors;
  onRecalculate?: (dimensions: RoomDimensions, factors: RoomIndoorFactors, targetAch: number) => void;
}

export const IndoorAirGuide: React.FC<IndoorAirGuideProps> = ({
  initialGuidance,
  initialDimensions = { length_m: 5.0, width_m: 4.0, height_m: 2.8 },
  initialFactors = {
    has_kitchen_chimney: true,
    burns_incense_agarbatti: false,
    has_unsealed_balcony: true,
  },
  onRecalculate,
}) => {
  const [lengthM, setLengthM] = useState<number>(initialDimensions.length_m);
  const [widthM, setWidthM] = useState<number>(initialDimensions.width_m);
  const [heightM, setHeightM] = useState<number>(initialDimensions.height_m);
  const [targetAch, setTargetAch] = useState<number>(initialGuidance.target_ach || 5.0);
  const [hasChimney, setHasChimney] = useState<boolean>(initialFactors.has_kitchen_chimney);
  const [burnsIncense, setBurnsIncense] = useState<boolean>(initialFactors.burns_incense_agarbatti);
  const [unsealedBalcony, setUnsealedBalcony] = useState<boolean>(initialFactors.has_unsealed_balcony);

  // Local deterministic calculations for immediate feedback
  const localVolumeM3 = Math.round(lengthM * widthM * heightM * 10) / 10;
  const localCADRM3PerHr = initialGuidance.required_cadr_m3_per_hr;
  const localCADRCFM = initialGuidance.required_cadr_cfm;

  const handleApplyChanges = (e: React.FormEvent) => {
    e.preventDefault();
    if (onRecalculate) {
      onRecalculate(
        { length_m: lengthM, width_m: widthM, height_m: heightM },
        {
          has_kitchen_chimney: hasChimney,
          burns_incense_agarbatti: burnsIncense,
          has_unsealed_balcony: unsealedBalcony,
        },
        targetAch
      );
    }
  };

  return (
    <section
      aria-labelledby="indoor-air-guide-title"
      className="bg-[var(--bg-surface)] p-5 sm:p-6 rounded-2xl border border-[var(--border-subtle)] shadow-xs space-y-6 transition-colors"
    >
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-teal-50 text-teal-700 dark:bg-teal-950 dark:text-teal-400">
              <Wind className="w-4 h-4" strokeWidth={1.75} aria-hidden="true" />
            </span>
            <h2 id="indoor-air-guide-title" className="text-lg sm:text-xl font-bold text-[var(--text-primary)]">
              3. Indoor Air Quality & CADR Action Engine
            </h2>
          </div>
          <p className="text-xs text-[var(--text-secondary)] mt-1">
            Deterministic Clean Air Delivery Rate (CADR), envelope infiltration control, and scientific plant footnotes.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Half: Interactive Room CADR Form */}
        <form
          onSubmit={handleApplyChanges}
          className="p-4 sm:p-5 bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded-xl space-y-4 flex flex-col justify-between"
        >
          <div>
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-1 mb-3">
              <h3 className="text-sm font-bold text-[var(--text-primary)]">
                Room Sizing & Household Environmental Factors
              </h3>
              <span className="text-xs text-[var(--text-secondary)] font-mono tabular-nums">
                V = {localVolumeM3} m³ ({Math.round(localVolumeM3 * 35.3147)} ft³)
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div>
                <label htmlFor="room-length" className="block text-xs font-semibold text-[var(--text-secondary)] mb-1">
                  Length (m)
                </label>
                <input
                  id="room-length"
                  type="number"
                  step="0.1"
                  min="1.0"
                  max="20.0"
                  value={lengthM}
                  onChange={(e) => setLengthM(Math.max(1.0, parseFloat(e.target.value) || 1.0))}
                  className="w-full min-h-[44px] px-3 py-1.5 text-xs bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 text-[var(--text-primary)] font-mono tabular-nums"
                />
              </div>

              <div>
                <label htmlFor="room-width" className="block text-xs font-semibold text-[var(--text-secondary)] mb-1">
                  Width (m)
                </label>
                <input
                  id="room-width"
                  type="number"
                  step="0.1"
                  min="1.0"
                  max="20.0"
                  value={widthM}
                  onChange={(e) => setWidthM(Math.max(1.0, parseFloat(e.target.value) || 1.0))}
                  className="w-full min-h-[44px] px-3 py-1.5 text-xs bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 text-[var(--text-primary)] font-mono tabular-nums"
                />
              </div>

              <div>
                <label htmlFor="room-height" className="block text-xs font-semibold text-[var(--text-secondary)] mb-1">
                  Height (m)
                </label>
                <input
                  id="room-height"
                  type="number"
                  step="0.1"
                  min="1.0"
                  max="10.0"
                  value={heightM}
                  onChange={(e) => setHeightM(Math.max(1.0, parseFloat(e.target.value) || 1.0))}
                  className="w-full min-h-[44px] px-3 py-1.5 text-xs bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 text-[var(--text-primary)] font-mono tabular-nums"
                />
              </div>

              <div>
                <label htmlFor="target-ach" className="block text-xs font-semibold text-[var(--text-secondary)] mb-1">
                  Target ACH
                </label>
                <select
                  id="target-ach"
                  value={targetAch}
                  onChange={(e) => setTargetAch(parseFloat(e.target.value))}
                  className="w-full min-h-[44px] px-2 py-1.5 text-xs bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 text-[var(--text-primary)] font-semibold"
                >
                  <option value={3}>3.0 ACH (Normal)</option>
                  <option value={5}>5.0 ACH (Smog Season - Rec.)</option>
                  <option value={6}>6.0 ACH (Higher filtration target)</option>
                </select>
              </div>
            </div>

            {/* Environmental Checkboxes */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-3 mt-3 border-t border-[var(--border-subtle)]">
              <label className="flex items-center gap-2 text-xs text-[var(--text-primary)] cursor-pointer min-h-[44px] px-1">
                <input
                  type="checkbox"
                  checked={hasChimney}
                  onChange={(e) => setHasChimney(e.target.checked)}
                  className="h-4 w-4 text-teal-600 rounded border-[var(--border-subtle)] focus:ring-teal-500"
                />
                <span>Kitchen Chimney Present</span>
              </label>

              <label className="flex items-center gap-2 text-xs text-[var(--text-primary)] cursor-pointer min-h-[44px] px-1">
                <input
                  type="checkbox"
                  checked={burnsIncense}
                  onChange={(e) => setBurnsIncense(e.target.checked)}
                  className="h-4 w-4 text-teal-600 rounded border-[var(--border-subtle)] focus:ring-teal-500"
                />
                <span>Burns Incense / Agarbatti</span>
              </label>

              <label className="flex items-center gap-2 text-xs text-[var(--text-primary)] cursor-pointer min-h-[44px] px-1">
                <input
                  type="checkbox"
                  checked={unsealedBalcony}
                  onChange={(e) => setUnsealedBalcony(e.target.checked)}
                  className="h-4 w-4 text-teal-600 rounded border-[var(--border-subtle)] focus:ring-teal-500"
                />
                <span>Unsealed Balcony / Doors</span>
              </label>
            </div>
          </div>

          <button
            type="submit"
            className="w-full min-h-[44px] px-4 py-2 bg-teal-700 hover:bg-teal-800 dark:bg-teal-600 dark:hover:bg-teal-500 text-white text-xs font-bold rounded-xl transition-colors shadow-xs focus:outline-none focus:ring-2 focus:ring-teal-500 cursor-pointer"
          >
            Update CADR & Sealing Advisory
          </button>
        </form>

        {/* Right Half: Deterministic Outputs */}
        <div className="space-y-4 flex flex-col justify-between">
          {/* CADR Sizing Card (Theme-Corrected: Light bg-[#ECFDF5] text-[#065F46] border-[#A7F3D0] · Dark dark:bg-[#0B2927] dark:text-[#5EEAD4] dark:border-[#115E59]) */}
          <div className="p-4 bg-[#ECFDF5] text-[#065F46] border border-[#A7F3D0] dark:bg-[#0B2927] dark:text-[#5EEAD4] dark:border-[#115E59] rounded-xl space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-xs uppercase tracking-wide font-bold flex items-center gap-1.5 text-[#065F46] dark:text-[#5EEAD4]">
                <CheckCircle2 className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" strokeWidth={1.75} aria-hidden="true" />
                Required Air Purifier CADR
              </span>
              <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-teal-100 dark:bg-teal-900 text-teal-800 dark:text-teal-200">
                Target: {targetAch} ACH
              </span>
            </div>

            <div className="flex items-baseline gap-3">
              <div className="text-3xl sm:text-4xl font-black font-mono tabular-nums text-[#065F46] dark:text-[#5EEAD4]">
                {localCADRM3PerHr} <span className="text-base font-normal">m³/h</span>
              </div>
              <div className="text-sm font-semibold text-teal-800 dark:text-teal-300 font-mono tabular-nums">
                ({localCADRCFM} CFM)
              </div>
            </div>

            <p className="text-xs pt-1 border-t border-[#A7F3D0] dark:border-[#115E59] text-[#065F46] dark:text-[#5EEAD4]">
              Sized for {localVolumeM3} m³ room volume ({lengthM}m × {widthM}m × {heightM}m). Provides {targetAch} full room air changes per hour.
            </p>
          </div>

          {/* Action & Sealing Card */}
          <div className="p-4 bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded-xl space-y-2.5">
            <div>
              <div className="text-xs uppercase tracking-wide text-[var(--text-secondary)] font-bold flex items-center gap-1.5">
                <ShieldAlert className="w-3.5 h-3.5 text-amber-600" strokeWidth={1.75} aria-hidden="true" />
                Envelope Infiltration & Sealing
              </div>
              <p className="text-xs text-[var(--text-primary)] mt-1 leading-relaxed">
                {unsealedBalcony
                  ? "Seal entrance and balcony gaps with door sweeps and weatherstripping; reduction depends on leakage and ventilation."
                  : initialGuidance.sealing_and_source_guidance}
              </p>
            </div>

            <div className="pt-2 border-t border-[var(--border-subtle)]">
              <div className="text-xs uppercase tracking-wide text-[var(--text-secondary)] font-bold">
                Diurnal Ventilation Window
              </div>
              <p className="text-xs text-[var(--text-primary)] mt-0.5 leading-relaxed">
                {initialGuidance.ventilation_recommendation ||
                  "Ventilate exclusively during peak solar heating (1:00 PM – 3:30 PM) when atmospheric mixing layer expands and surface PM2.5 drops. Seal tightly during morning and night thermal inversions."}
              </p>
            </div>

            {burnsIncense && (
              <div className="p-2.5 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 rounded-lg text-xs text-red-900 dark:text-red-200 font-medium flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" strokeWidth={1.75} aria-hidden="true" />
                <div>
                  <strong>Indoor Agarbatti Alert:</strong> Burning incense adds indoor particulate pollution. Stop burning it and control indoor sources before relying on filtration.
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Mandatory Scientific Footnote on Plants (Theme-Corrected: Light bg-[#FFFBEB] text-[#78350F] border-[#FDE68A] · Dark dark:bg-[#2E1E05] dark:text-[#FDE68A] dark:border-[#92400E]) */}
      <div
        role="note"
        aria-label="Scientific Note on Air-Purifying Plants"
        className="p-3.5 bg-[#FFFBEB] text-[#78350F] border border-[#FDE68A] dark:bg-[#2E1E05] dark:text-[#FDE68A] dark:border-[#92400E] rounded-xl text-xs leading-relaxed"
      >
        <strong className="block font-bold text-[#78350F] dark:text-[#FDE68A] mb-1 flex items-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5 text-amber-700 dark:text-amber-400" strokeWidth={1.75} aria-hidden="true" />
          Scientific Footnote on NASA Air-Purifying Plants (Areca Palm, Snake Plant, Peace Lily):
        </strong>
        {initialGuidance.plants_footnote ||
          "The 1989 NASA Clean Air Study evaluated sealed, fan-assisted chambers over 24 hours. In real-world homes with standard air exchange rates (0.5–2.0 ACH), potted plants achieve negligible PM2.5 particulate reduction (<1%) and do NOT replace mechanical HEPA purifiers. Potted plants provide valuable biophilic and psychological benefits, but zero defense against severe particulate smog."}
      </div>

      {/* Expandable Show the Math Drawer */}
      <MathDrawer title="Show the Math: Room Volume, CADR Formula & ACH Benchmarks">
        <div>
          <strong className="text-[var(--text-primary)]">1. Room Volume Calculation:</strong>
          <code className="block bg-[var(--bg-surface)] p-2 rounded border border-[var(--border-subtle)] font-mono tabular-nums mt-1 text-[var(--text-primary)]">
            Volume (m³) = Length ({lengthM}m) × Width ({widthM}m) × Height ({heightM}m) = {localVolumeM3} m³
          </code>
        </div>

        <div>
          <strong className="text-[var(--text-primary)]">2. Deterministic CADR Formula:</strong>
          <code className="block bg-[var(--bg-surface)] p-2 rounded border border-[var(--border-subtle)] font-mono tabular-nums mt-1 text-[var(--text-primary)]">
            CADR (m³/h) = Volume ({initialGuidance.room_volume_m3} m³) × Target ACH ({initialGuidance.target_ach} h⁻¹) × configured source adjustment = {localCADRM3PerHr} m³/h
          </code>
          <code className="block bg-[var(--bg-surface)] p-2 rounded border border-[var(--border-subtle)] font-mono tabular-nums mt-1 text-[var(--text-primary)]">
            CADR (CFM) = {localCADRM3PerHr} m³/h × 0.5886 = {localCADRCFM} CFM
          </code>
        </div>

        <div className="p-2.5 bg-teal-50 dark:bg-teal-950/40 border border-teal-200 dark:border-teal-800 rounded-lg text-teal-950 dark:text-teal-200">
          <strong>Target ACH Benchmarks (AHAM AC-1 / ANSI Standards):</strong>
          <ul className="list-disc list-inside mt-1 space-y-0.5">
            <li>2.0–3.0 ACH: Maintenance level for sealed rooms on moderate air days.</li>
            <li>4.0–5.0 ACH: Mandatory recommendation for severe North Indian winter smog episodes (AQI &gt; 300).</li>
            <li>6.0+ ACH: Clinical requirement for acute asthma, COPD, and immunocompromised family members.</li>
          </ul>
        </div>
      </MathDrawer>
    </section>
  );
};
