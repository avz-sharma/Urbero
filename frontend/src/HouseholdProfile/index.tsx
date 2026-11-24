import React from "react";
import { m } from "motion/react";
import { Users, MapPin } from "lucide-react";
import type {
  RoomDimensions,
  RoomIndoorFactors,
  ScheduledActivity,
} from "../api/types";
import { snappySpring } from "../lib/motion";

export interface PresetProfile {
  id: string;
  name: string;
  city: string;
  summary: string;
  commute_distance_km: number;
  room_dimensions: RoomDimensions;
  indoor_factors: RoomIndoorFactors;
  activities: ScheduledActivity[];
  memberChips: string[];
}

export const INDIAN_PRESETS: PresetProfile[] = [
  {
    id: "south-delhi",
    activities: [
      {
        id: "senior-walk",
        name: "Morning walk",
        member_name: "Grandfather",
        age_group: "senior",
        intensity: "moderate",
        scheduled_start_hour: 7,
        scheduled_end_hour: 8,
        is_outdoor: true,
        is_flexible: true,
        indoor_purifier_active: false,
      },
      {
        id: "school",
        name: "School commute",
        member_name: "Schoolchild",
        age_group: "child",
        intensity: "light",
        scheduled_start_hour: 7.5,
        scheduled_end_hour: 8,
        is_outdoor: true,
        is_flexible: false,
        indoor_purifier_active: false,
      },
    ],
    name: "South Delhi Joint Family",
    city: "Delhi",
    summary: "Asthmatic grandfather, 8yo schoolkid, Gurgaon highway commuter.",
    commute_distance_km: 18.0,
    room_dimensions: { length_m: 5.5, width_m: 4.2, height_m: 2.8 },
    indoor_factors: {
      has_kitchen_chimney: true,
      burns_incense_agarbatti: false,
      has_unsealed_balcony: true,
    },
    memberChips: [
      "Dada Ji (72 · Asthmatic)",
      "Aarav (8 · Schoolkid)",
      "Rahul (41 · Commuter)",
    ],
  },
  {
    id: "mumbai-couple",
    activities: [
      {
        id: "evening-jog",
        name: "Evening jog",
        member_name: "Adult",
        age_group: "adult",
        intensity: "heavy",
        scheduled_start_hour: 18,
        scheduled_end_hour: 19,
        is_outdoor: true,
        is_flexible: true,
        indoor_purifier_active: false,
      },
    ],
    name: "Andheri Mumbai Working Couple",
    city: "Mumbai",
    summary:
      "Working professionals, local train & auto commute, evening joggers.",
    commute_distance_km: 12.0,
    room_dimensions: { length_m: 4.5, width_m: 3.8, height_m: 2.7 },
    indoor_factors: {
      has_kitchen_chimney: false,
      burns_incense_agarbatti: true,
      has_unsealed_balcony: false,
    },
    memberChips: [
      "Priya (30 · Office Commuter)",
      "Vikram (32 · Evening Jogger)",
    ],
  },
  {
    id: "kolkata-seniors",
    activities: [
      {
        id: "senior-walk",
        name: "Park walk",
        member_name: "Senior couple",
        age_group: "senior",
        intensity: "moderate",
        scheduled_start_hour: 7,
        scheduled_end_hour: 8,
        is_outdoor: true,
        is_flexible: true,
        indoor_purifier_active: false,
      },
    ],
    name: "Salt Lake Kolkata Senior Couple",
    city: "Kolkata",
    summary:
      "Retired senior couple, daily morning park walkers, naturally ventilated flat.",
    commute_distance_km: 6.0,
    room_dimensions: { length_m: 4.8, width_m: 3.5, height_m: 3.0 },
    indoor_factors: {
      has_kitchen_chimney: true,
      burns_incense_agarbatti: true,
      has_unsealed_balcony: true,
    },
    memberChips: ["Amit (68 · Retired)", "Jaya (65 · Retired)"],
  },
];

export interface HouseholdProfileProps {
  selectedPresetId: string | null;
  onSelectPreset: (preset: PresetProfile) => void;
}

export const HouseholdProfile: React.FC<HouseholdProfileProps> = ({
  selectedPresetId,
  onSelectPreset,
}) => {
  return (
    <section
      aria-labelledby="household-presets-heading"
      className="bg-[var(--bg-surface)] p-5 sm:p-6 rounded-2xl border border-[var(--border-subtle)] shadow-xs transition-colors"
    >
      <div className="mb-5">
        <div className="flex items-center gap-2">
          <span className="p-1.5 rounded-lg bg-teal-50 text-teal-700 dark:bg-teal-950 dark:text-teal-400">
            <Users className="w-4 h-4" strokeWidth={1.75} aria-hidden="true" />
          </span>
          <h2
            id="household-presets-heading"
            className="text-lg sm:text-xl font-bold text-[var(--text-primary)]"
          >
            1. Indian Household Presets
          </h2>
        </div>
        <p className="text-xs text-[var(--text-secondary)] mt-1">
          Optional example household profiles. Your chosen location stays
          unchanged.
        </p>
      </div>

      <div
        className="grid grid-cols-1 md:grid-cols-3 gap-4"
        role="radiogroup"
        aria-label="Household Preset Options"
      >
        {INDIAN_PRESETS.map((preset) => {
          const isSelected = selectedPresetId === preset.id;
          return (
            <button
              key={preset.id}
              type="button"
              role="radio"
              aria-checked={isSelected}
              onClick={() => onSelectPreset(preset)}
              className={`relative min-h-[44px] p-4 rounded-xl border-2 text-left transition-all focus:outline-none focus:ring-2 focus:ring-teal-500 flex flex-col justify-between ${
                isSelected
                  ? "border-teal-600 dark:border-teal-400 bg-teal-50/40 dark:bg-teal-950/20 shadow-xs"
                  : "border-[var(--border-subtle)] bg-[var(--bg-surface)] hover:border-gray-300 dark:hover:border-gray-700 hover:bg-[var(--bg-elevated)]"
              }`}
            >
              {isSelected && (
                <m.div
                  layoutId="preset-active-ring"
                  transition={snappySpring}
                  className="absolute inset-0 rounded-xl ring-2 ring-teal-500/50 pointer-events-none"
                />
              )}

              <div>
                <div className="flex justify-between items-start gap-2 mb-1.5">
                  <span className="font-bold text-sm text-[var(--text-primary)]">
                    {preset.name}
                  </span>
                  <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 bg-[var(--bg-elevated)] text-[var(--text-secondary)] rounded-md border border-[var(--border-subtle)] shrink-0">
                    <MapPin
                      className="w-3 h-3 text-teal-600 dark:text-teal-400"
                      strokeWidth={1.75}
                      aria-hidden="true"
                    />
                    {preset.city}
                  </span>
                </div>

                <div className="flex flex-wrap gap-1.5 mb-2.5">
                  {preset.memberChips.map((chip) => (
                    <span
                      key={chip}
                      className="text-[11px] font-medium px-2 py-0.5 rounded bg-teal-100/70 text-teal-900 dark:bg-teal-950/80 dark:text-teal-200"
                    >
                      {chip}
                    </span>
                  ))}
                </div>

                <p className="text-xs text-[var(--text-secondary)] italic leading-relaxed">
                  {preset.summary}
                </p>
              </div>

              <div className="mt-3 pt-2.5 border-t border-[var(--border-subtle)] text-[11px] text-[var(--text-secondary)] flex justify-between items-center">
                <span>Commute: {preset.commute_distance_km} km</span>
                <span className="text-teal-700 dark:text-teal-400 font-semibold">
                  {isSelected ? "Active Profile" : "Use household preset"}
                </span>
              </div>
            </button>
          );
        })}
      </div>
    </section>
  );
};
