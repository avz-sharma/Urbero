import { useId, useRef, useState, type FormEvent } from "react";
import type { ScheduledActivity } from "../api/types";

export function formatHour(hour: number): string {
  const minutes = Math.round(hour * 60);
  return `${String(Math.floor(minutes / 60)).padStart(2, "0")}:${String(minutes % 60).padStart(2, "0")}`;
}

function readHour(value: string): number {
  const [hours, minutes] = value.split(":").map(Number);
  return hours + minutes / 60;
}

const field =
  "min-h-[44px] w-full rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-elevated)] px-3";
const button =
  "min-h-[44px] rounded-lg border border-[var(--border-subtle)] px-4 font-semibold";

export function ScheduleEditor({
  activities,
  onApply,
  busy,
}: {
  activities: ScheduledActivity[];
  onApply: (activities: ScheduledActivity[]) => void;
  busy: boolean;
}) {
  const id = useId();
  const sequence = useRef(0);
  const [draft, setDraft] = useState(activities);
  const [error, setError] = useState("");

  function update(activityId: string, patch: Partial<ScheduledActivity>) {
    setDraft((rows) =>
      rows.map((row) => (row.id === activityId ? { ...row, ...patch } : row)),
    );
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (
      draft.some(
        (activity) =>
          !activity.name.trim() ||
          !activity.member_name.trim() ||
          !Number.isFinite(activity.scheduled_start_hour) ||
          !Number.isFinite(activity.scheduled_end_hour) ||
          activity.scheduled_end_hour <= activity.scheduled_start_hour,
      )
    ) {
      setError(
        "Enter a name and household member for each activity. End time must be after start time on the same day.",
      );
      return;
    }
    setError("");
    onApply(
      draft.map((activity) => ({
        ...activity,
        name: activity.name.trim(),
        member_name: activity.member_name.trim(),
      })),
    );
  }

  return (
    <form
      onSubmit={submit}
      aria-labelledby={id}
      className="space-y-4 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-5"
    >
      <h2 id={id} className="text-lg font-bold">
        What is your current household schedule?
      </h2>
      <p className="text-sm text-[var(--text-secondary)]">
        Add your usual activities and local times. Mark fixed commitments so the
        planner keeps their time.
      </p>
      {draft.map((activity, index) => (
        <fieldset
          key={activity.id}
          className="space-y-3 rounded-lg border border-[var(--border-subtle)] p-3"
        >
          <legend className="px-2 font-semibold">Activity {index + 1}</legend>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <label>
              Activity name
              <input
                className={field}
                required
                maxLength={80}
                placeholder="School pickup"
                value={activity.name}
                onChange={(event) =>
                  update(activity.id, { name: event.target.value })
                }
              />
            </label>
            <label>
              Household member
              <input
                className={field}
                required
                maxLength={80}
                value={activity.member_name}
                onChange={(event) =>
                  update(activity.id, { member_name: event.target.value })
                }
              />
            </label>
            <label>
              Start time
              <input
                className={field}
                type="time"
                required
                value={
                  Number.isFinite(activity.scheduled_start_hour)
                    ? formatHour(activity.scheduled_start_hour)
                    : ""
                }
                onChange={(event) =>
                  update(activity.id, {
                    scheduled_start_hour: readHour(event.target.value),
                  })
                }
              />
            </label>
            <label>
              End time
              <input
                className={field}
                type="time"
                required
                value={
                  activity.scheduled_end_hour === 24
                    ? "00:00"
                    : Number.isFinite(activity.scheduled_end_hour)
                      ? formatHour(activity.scheduled_end_hour)
                      : ""
                }
                onChange={(event) =>
                  update(activity.id, {
                    scheduled_end_hour:
                      event.target.value === "00:00"
                        ? 24
                        : readHour(event.target.value),
                  })
                }
              />
            </label>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <label className="flex min-h-[44px] items-center gap-2">
              <input
                type="checkbox"
                checked={activity.is_outdoor}
                onChange={(event) =>
                  update(activity.id, { is_outdoor: event.target.checked })
                }
              />{" "}
              Outdoors
            </label>
            <label className="flex min-h-[44px] items-center gap-2">
              <input
                type="checkbox"
                checked={!activity.is_flexible}
                onChange={(event) =>
                  update(activity.id, { is_flexible: !event.target.checked })
                }
              />{" "}
              Fixed time
            </label>
            <button
              className={button}
              type="button"
              aria-label={`Remove activity ${index + 1}`}
              onClick={() =>
                setDraft((rows) => rows.filter((row) => row.id !== activity.id))
              }
            >
              Remove
            </button>
          </div>
        </fieldset>
      ))}
      {error && <p role="alert">{error}</p>}
      <div className="flex flex-wrap gap-3">
        <button
          className={button}
          type="button"
          disabled={draft.length >= 32}
          onClick={() => {
            const activityId = `${id}-activity-${++sequence.current}`;
            setDraft((rows) => [
              ...rows,
              {
                id: activityId,
                name: "",
                member_name: "Household member",
                age_group: "adult",
                intensity: "moderate",
                scheduled_start_hour: 7,
                scheduled_end_hour: 8,
                is_outdoor: true,
                is_flexible: true,
                indoor_purifier_active: false,
              },
            ]);
          }}
        >
          Add activity
        </button>
        <button
          className={`${button} bg-teal-700 text-white disabled:opacity-60`}
          type="submit"
          disabled={busy || (!draft.length && !activities.length)}
        >
          {busy ? "Updating plan…" : "Apply schedule"}
        </button>
      </div>
    </form>
  );
}
