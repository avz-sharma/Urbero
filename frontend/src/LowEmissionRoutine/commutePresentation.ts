import { Bike, Car, Footprints, Train } from "lucide-react";
import type { CommuteModeComparison } from "../api/types";

function getModeIcon(mode: string) {
  switch (mode) {
    case "metro":
    case "train":
      return Train;
    case "cycling":
    case "bicycle":
      return Bike;
    case "walking":
      return Footprints;
    default:
      return Car;
  }
}

export function getCommutePresentation(option: CommuteModeComparison) {
  const mode = option.mode.toLowerCase();
  const note = option.planet_vs_lungs_note.toLowerCase();
  return {
    ModeIcon: getModeIcon(mode),
    isOptimal: mode === "metro" || note.includes("win-win"),
    isConflict: note.includes("hazard") || note.includes("conflict"),
  };
}
