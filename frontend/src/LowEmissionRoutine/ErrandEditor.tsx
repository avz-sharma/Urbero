import { useId, useState } from "react";
import type { ErrandStop } from "../api/types";
import { formatHour, readHour } from "./ScheduleEditor";

const field =
  "min-h-[44px] w-full rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-elevated)] px-3";
const button =
  "min-h-[44px] rounded-lg border border-[var(--border-subtle)] px-4 font-semibold";

export function ErrandEditor({
  stops,
  onApply,
  busy,
  serverError,
}: {
  stops: ErrandStop[];
  onApply: (stops: ErrandStop[]) => void;
  busy: boolean;
  serverError: string | null;
}) {
  const id = useId();
  const [draft, setDraft] = useState(stops);
  const [error, setError] = useState("");
  const update = (stopId: string, patch: Partial<ErrandStop>) => {
    setDraft((rows) =>
      rows.map((row) => (row.id === stopId ? { ...row, ...patch } : row)),
    );
  };

  return (
    <form
      className="space-y-3 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-4"
      aria-labelledby={`${id}-title`}
      aria-describedby={error || serverError ? `${id}-error` : undefined}
      onSubmit={(event) => {
        event.preventDefault();
        if (
          draft.some(
            (row) =>
              !row.name.trim() ||
              row.duration_minutes <= 0 ||
              row.distance_from_home_km <= 0 ||
              (row.window_open_hour != null &&
                row.window_close_hour != null &&
                row.window_close_hour <= row.window_open_hour),
          )
        ) {
          setError(
            "Enter a name, positive distance and duration, and a closing time after opening for each errand.",
          );
          return;
        }
        setError("");
        onApply(draft.map((row) => ({ ...row, name: row.name.trim() })));
      }}
    >
      <h3 id={`${id}-title`} className="font-bold">
        Combine errands
      </h3>
      <p className="text-sm">
        Add up to four stops. Enter opening and completion times when a stop has
        a fixed window.
      </p>
      {draft.map((stop, index) => (
        <fieldset
          key={stop.id}
          className="grid gap-2 rounded-lg border border-[var(--border-subtle)] p-3 text-sm sm:grid-cols-2"
        >
          <legend className="font-semibold">Stop {index + 1}</legend>
          <label>
            Stop {index + 1} name
            <input
              className={field}
              maxLength={80}
              required
              value={stop.name}
              onChange={(event) =>
                update(stop.id, { name: event.target.value })
              }
            />
          </label>
          <label>
            Stop {index + 1} category
            <select
              className={field}
              value={stop.category}
              onChange={(event) => {
                const category = event.target.value;
                if (
                  category === "groceries" ||
                  category === "pharmacy" ||
                  category === "bank" ||
                  category === "school" ||
                  category === "other"
                )
                  update(stop.id, { category });
              }}
            >
              <option value="groceries">Groceries</option>
              <option value="pharmacy">Pharmacy</option>
              <option value="bank">Bank</option>
              <option value="school">School pickup</option>
              <option value="other">Other</option>
            </select>
          </label>
          <label>
            Stop {index + 1} distance from home (km)
            <input
              className={field}
              type="number"
              min="0.01"
              step="any"
              required
              value={stop.distance_from_home_km || ""}
              onChange={(event) =>
                update(stop.id, {
                  distance_from_home_km: Number(event.target.value),
                })
              }
            />
          </label>
          <label>
            Stop {index + 1} duration (min)
            <input
              className={field}
              type="number"
              min="1"
              step="any"
              required
              value={stop.duration_minutes || ""}
              onChange={(event) =>
                update(stop.id, {
                  duration_minutes: Number(event.target.value),
                })
              }
            />
          </label>
          <label>
            Stop {index + 1} opens
            <input
              className={field}
              type="time"
              value={
                stop.window_open_hour == null
                  ? ""
                  : formatHour(stop.window_open_hour)
              }
              onChange={(event) =>
                update(stop.id, {
                  window_open_hour: event.target.value
                    ? readHour(event.target.value)
                    : null,
                })
              }
            />
          </label>
          <label>
            Stop {index + 1} finish by
            <input
              className={field}
              type="time"
              value={
                stop.window_close_hour == null
                  ? ""
                  : formatHour(stop.window_close_hour)
              }
              onChange={(event) =>
                update(stop.id, {
                  window_close_hour: event.target.value
                    ? readHour(event.target.value)
                    : null,
                })
              }
            />
          </label>
          <button
            type="button"
            className={button}
            onClick={() =>
              setDraft((rows) => rows.filter((row) => row.id !== stop.id))
            }
          >
            Remove stop {index + 1}
          </button>
        </fieldset>
      ))}
      {(error || serverError) && (
        <p id={`${id}-error`} role="alert">
          {error || serverError}
        </p>
      )}
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          className={button}
          disabled={draft.length >= 4}
          onClick={() =>
            setDraft([
              ...draft,
              {
                id: crypto.randomUUID(),
                name: "",
                category: "groceries",
                distance_from_home_km: 0,
                duration_minutes: 0,
              },
            ])
          }
        >
          Add errand
        </button>
        <button
          type="submit"
          className={button}
          disabled={busy || (!draft.length && !stops.length)}
        >
          Apply errands
        </button>
      </div>
    </form>
  );
}
