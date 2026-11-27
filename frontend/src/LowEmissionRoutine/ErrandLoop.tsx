import type { MergedErrandsResult } from "../api/types";
import { MathDrawer } from "../common/MathDrawer";
import { formatHour } from "./ScheduleEditor";

export function ErrandLoop({ result }: { result: MergedErrandsResult }) {
  const change = result.pm25_dose_reduction_percent;
  const dose =
    change === 0
      ? "Unchanged"
      : `${Math.abs(change)}% ${change > 0 ? "lower" : "higher"}`;

  return (
    <section
      aria-label="Errand loop"
      className="space-y-4 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-5"
    >
      <h3 className="font-bold">
        Errand Consolidation Loop ({result.ordered_stops.length} Stops)
      </h3>
      <dl className="grid gap-3 text-sm sm:grid-cols-2">
        <div>
          <dt>Estimated trip time</dt>
          <dd>
            {formatHour(result.recommended_start_hour)}–
            {formatHour(result.recommended_end_hour)}
          </dd>
        </div>
        <div>
          <dt>Travel mode</dt>
          <dd>
            {result.travel_mode === "petrol_2w"
              ? "Petrol two-wheeler"
              : result.travel_mode.replace(/_/g, " ")}
          </dd>
        </div>
        <div>
          <dt>Separate trips</dt>
          <dd>{result.baseline_separate_distance_km} km</dd>
        </div>
        <div>
          <dt>Merged loop</dt>
          <dd>
            {result.merged_loop_distance_km} km ({result.distance_saved_km} km
            saved)
          </dd>
        </div>
        <div>
          <dt>Tailpipe CO₂ avoided</dt>
          <dd>{result.tailpipe_co2_saved_grams} g</dd>
        </div>
        <div>
          <dt>Estimated inhaled PM₂.₅</dt>
          <dd>{dose}</dd>
        </div>
      </dl>
      <ol className="list-decimal space-y-1 pl-5 text-sm">
        {result.ordered_stops.map((stop) => (
          <li key={stop.id}>
            {stop.name} ({stop.duration_minutes} min)
          </li>
        ))}
      </ol>
      <MathDrawer title="Show the Math: Errand distances and emissions">
        <p>
          Inter-stop distances are approximated from distances to home. Ordering
          accounts for travel, waiting and stop times.
        </p>
        <p>
          Distance saved = {result.baseline_separate_distance_km} km −{" "}
          {result.merged_loop_distance_km} km = {result.distance_saved_km} km.
        </p>
        <p>
          CO₂ avoided = {result.distance_saved_km} km ×{" "}
          {result.emissions_factor_g_per_km} g/km ={" "}
          {result.tailpipe_co2_saved_grams} g.
        </p>
        <p>
          Estimated inhaled PM₂.₅ changes from {result.baseline_inhaled_pm25_ug}{" "}
          µg to {result.optimized_inhaled_pm25_ug} µg.
        </p>
      </MathDrawer>
    </section>
  );
}
