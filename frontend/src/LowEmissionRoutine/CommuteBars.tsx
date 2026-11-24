import type { CommuteModeComparison } from "../api/types";
import { getModeIcon } from "./commuteIcons";

export default function CommuteBars({ commuteOptions }: { commuteOptions: CommuteModeComparison[] }) {
  const maxCO2 = Math.max(
    ...commuteOptions.map((c) => c.tailpipe_co2_grams),
    1,
  );
  const maxPM25 = Math.max(
    ...commuteOptions.map((c) => c.personal_inhaled_pm25_ug),
    1,
  );


  return (
          <div className="space-y-3">
            {commuteOptions.map((c) => {
              const isOptimal =
                c.mode.toLowerCase() === "metro" ||
                c.planet_vs_lungs_note.toLowerCase().includes("win-win");
              const isConflict =
                c.planet_vs_lungs_note.toLowerCase().includes("hazard") ||
                c.planet_vs_lungs_note.toLowerCase().includes("conflict");
              const ModeIcon = getModeIcon(c.mode);
              const co2Percent = Math.round(
                (c.tailpipe_co2_grams / maxCO2) * 100,
              );
              const pm25Percent = Math.round(
                (c.personal_inhaled_pm25_ug / maxPM25) * 100,
              );

              return (
                <div
                  key={c.mode}
                  className={`p-3 rounded-xl border transition-all space-y-2 ${
                    isOptimal
                      ? "border-teal-400 dark:border-teal-700 bg-[#ECFDF5]/85 text-[#0F1B1D] dark:bg-[#052E24]/60 dark:text-[#F0F5F4]"
                      : isConflict
                        ? "border-amber-400 dark:border-amber-700 bg-[#FEF2F2]/85 text-[#0F1B1D] dark:bg-[#310B0E]/60 dark:text-[#F0F5F4]"
                        : "border-[var(--border-subtle)] bg-[var(--bg-surface)] text-[var(--text-primary)]"
                  }`}
                >
                  <div className="flex justify-between items-center flex-wrap gap-1">
                    <div className="flex items-center gap-1.5 font-bold text-xs text-[var(--text-primary)]">
                      <ModeIcon
                        className="w-4 h-4 text-teal-600 dark:text-teal-400"
                        strokeWidth={1.75}
                        aria-hidden="true"
                      />
                      <span>{c.label}</span>
                      {isOptimal && (
                        <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-teal-200 dark:bg-teal-800 text-teal-900 dark:text-teal-100">
                          Optimal Win-Win
                        </span>
                      )}
                      {isConflict && (
                        <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-amber-200 dark:bg-amber-900 text-amber-900 dark:text-amber-100">
                          Planet vs. Lungs Conflict
                        </span>
                      )}
                    </div>
                    <span className="text-[11px] font-mono tabular-nums text-[var(--text-secondary)]">
                      {c.duration_minutes} min duration
                    </span>
                  </div>

                  {/* CO2 Proportional Bar */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-[11px] text-[var(--text-secondary)]">
                      <span>Transport CO₂</span>
                      <span className="font-mono tabular-nums font-semibold">
                        {c.tailpipe_co2_grams} g
                      </span>
                    </div>
                    <div className="w-full h-2 bg-gray-200 dark:bg-gray-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-emerald-500 rounded-full transition-all duration-300"
                        style={{ width: `${Math.max(co2Percent, 2)}%` }}
                        aria-hidden="true"
                      />
                    </div>
                  </div>

                  {/* PM2.5 Inhaled Dose Proportional Bar */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-[11px] text-[var(--text-secondary)]">
                      <span>Inhaled PM₂.₅ Dose</span>
                      <span className="font-mono tabular-nums font-bold text-red-600 dark:text-red-400">
                        {c.personal_inhaled_pm25_ug} µg
                      </span>
                    </div>
                    <div className="w-full h-2 bg-gray-200 dark:bg-gray-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-rose-500 rounded-full transition-all duration-300"
                        style={{ width: `${Math.max(pm25Percent, 2)}%` }}
                        aria-hidden="true"
                      />
                    </div>
                  </div>

                  <p className="text-[11px] text-[var(--text-secondary)] italic leading-relaxed pt-1">
                    {c.planet_vs_lungs_note}
                  </p>
                </div>
              );
            })}
          </div>
  );
}
