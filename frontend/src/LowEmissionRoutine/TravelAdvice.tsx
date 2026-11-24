import { useEffect, useId, useRef, useState, type FormEvent } from "react";
import type { components } from "../api/generated";
import type { ActiveLocation } from "../api/types";

type Advice = components["schemas"]["TravelAdviceResponse"];
const focus = {
  exposure: "Lower estimated particulate exposure",
  emissions: "Lower estimated transport emissions",
  time: "Shorter estimated trip time",
  balance: "A balance of exposure, emissions, and travel time",
};

export function TravelAdvice({
  location,
  defaultDistance,
}: {
  location: ActiveLocation;
  defaultDistance: number;
}) {
  const id = useId();
  const [question, setQuestion] = useState("");
  const [distance, setDistance] = useState(String(defaultDistance));
  const [result, setResult] = useState<Advice | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const pending = useRef<AbortController | null>(null);

  useEffect(() => () => pending.current?.abort(), []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!question.trim() || busy) return;
    const controller = new AbortController();
    pending.current = controller;
    setResult(null);
    setError("");
    setBusy(true);
    const body: components["schemas"]["TravelAdviceRequest"] = {
      latitude: location.lat,
      longitude: location.lon,
      distance_km: Number(distance),
      question: question.trim(),
    };
    try {
      const response = await fetch("/api/exposure/commute/advice", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: controller.signal,
      });
      if (!response.ok) throw new Error("Travel advice unavailable");
      const advice: Advice = await response.json();
      if (!controller.signal.aborted) setResult(advice);
    } catch {
      if (!controller.signal.aborted)
        setError("Travel advice is temporarily unavailable. Please try again.");
    } finally {
      if (!controller.signal.aborted) setBusy(false);
    }
  }

  return (
    <form
      onSubmit={submit}
      aria-labelledby={id}
      className="space-y-4 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-5"
    >
      <h2 id={id} className="text-lg font-bold">
        How should I travel?
      </h2>
      <p className="text-sm text-[var(--text-secondary)]">
        Ask about your priorities for a trip in {location.label}. Check local
        routes and service before leaving.
      </p>
      <label className="block">
        Travel question
        <textarea
          required
          maxLength={300}
          rows={2}
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="I need a quick commute and want to reduce smoke exposure."
          className="mt-1 w-full rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-elevated)] p-3"
        />
      </label>
      <label className="block">
        Trip distance (km)
        <input
          required
          type="number"
          min="0.1"
          max="200"
          step="any"
          value={distance}
          onChange={(event) => setDistance(event.target.value)}
          className="ml-2 min-h-[44px] w-24 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-elevated)] px-2"
        />
      </label>
      <button
        type="submit"
        disabled={busy || !question.trim()}
        className="min-h-[44px] rounded-lg bg-teal-700 px-4 font-semibold text-white disabled:opacity-60"
      >
        {busy ? "Comparing options…" : "Get travel advice"}
      </button>
      {error && <p role="alert">{error}</p>}
      {result && (
        <div
          role="status"
          className="space-y-2 rounded-lg bg-[var(--bg-elevated)] p-4"
        >
          <p className="font-bold">Consider {result.recommendation.label}</p>
          <p>
            {focus[result.priority]} ·{" "}
            {result.source !== "fallback_template"
              ? "AI-assisted suggestion"
              : "Rule-based suggestion"}
          </p>
          <p>
            Estimated for {result.recommendation.distance_km} km:{" "}
            {result.recommendation.duration_minutes} min,{" "}
            {result.recommendation.personal_inhaled_pm25_ug} µg inhaled PM2.5,{" "}
            {result.recommendation.tailpipe_co2_grams} g transport CO₂.
          </p>
          {result.smog_advisory && <p>{result.smog_advisory}</p>}
        </div>
      )}
    </form>
  );
}
