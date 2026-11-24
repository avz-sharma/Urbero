import type { ComponentType } from "react";
import type { LucideProps } from "lucide-react";
import {
  ShieldCheck,
  Wind,
  AlertCircle,
  AlertTriangle,
  OctagonAlert,
  Siren,
} from "lucide-react";

export interface AQIBandTheme {
  category: string;
  minAqi: number;
  maxAqi: number;
  icon: ComponentType<LucideProps>;
  light: {
    bg: string;
    text: string;
    border: string;
  };
  dark: {
    bg: string;
    text: string;
    border: string;
  };
}

export const CPCB_AQI_BANDS: Record<string, AQIBandTheme> = {
  Good: {
    category: "Good",
    minAqi: 0,
    maxAqi: 50,
    icon: ShieldCheck,
    light: { bg: "#ECFDF5", text: "#065F46", border: "#A7F3D0" },
    dark: { bg: "#052E24", text: "#6EE7B7", border: "#065F46" },
  },
  Satisfactory: {
    category: "Satisfactory",
    minAqi: 51,
    maxAqi: 100,
    icon: Wind,
    light: { bg: "#F7FEE7", text: "#3F6212", border: "#D9F99D" },
    dark: { bg: "#1A2E05", text: "#BEF264", border: "#3F6212" },
  },
  Moderate: {
    category: "Moderate",
    minAqi: 101,
    maxAqi: 200,
    icon: AlertCircle,
    light: { bg: "#FFFBEB", text: "#92400E", border: "#FDE68A" },
    dark: { bg: "#2E1E05", text: "#FCD34D", border: "#92400E" },
  },
  Poor: {
    category: "Poor",
    minAqi: 201,
    maxAqi: 300,
    icon: AlertTriangle,
    light: { bg: "#FFF7ED", text: "#9A3412", border: "#FDBA74" },
    dark: { bg: "#2F1406", text: "#FB923C", border: "#9A3412" },
  },
  "Very Poor": {
    category: "Very Poor",
    minAqi: 301,
    maxAqi: 400,
    icon: OctagonAlert,
    light: { bg: "#FEF2F2", text: "#991B1B", border: "#FCA5A5" },
    dark: { bg: "#310B0E", text: "#FCA5A5", border: "#991B1B" },
  },
  Severe: {
    category: "Severe",
    minAqi: 401,
    maxAqi: 500,
    icon: Siren,
    light: { bg: "#FAF5FF", text: "#6B21A8", border: "#D8B4FE" },
    dark: { bg: "#240B36", text: "#E9D5FF", border: "#7E22CE" },
  },
};

export function getAQIBand(categoryOrScore: string | number): AQIBandTheme {
  if (typeof categoryOrScore === "string") {
    const normalized = categoryOrScore.trim();
    if (CPCB_AQI_BANDS[normalized]) {
      return CPCB_AQI_BANDS[normalized];
    }
    // Case-insensitive fallback
    const key = Object.keys(CPCB_AQI_BANDS).find(
      (k) => k.toLowerCase() === normalized.toLowerCase()
    );
    if (key && CPCB_AQI_BANDS[key]) {
      return CPCB_AQI_BANDS[key];
    }
  }

  const score = typeof categoryOrScore === "number" ? categoryOrScore : parseFloat(categoryOrScore);
  if (isNaN(score)) return CPCB_AQI_BANDS["Moderate"];

  if (score <= 50) return CPCB_AQI_BANDS["Good"];
  if (score <= 100) return CPCB_AQI_BANDS["Satisfactory"];
  if (score <= 200) return CPCB_AQI_BANDS["Moderate"];
  if (score <= 300) return CPCB_AQI_BANDS["Poor"];
  if (score <= 400) return CPCB_AQI_BANDS["Very Poor"];
  return CPCB_AQI_BANDS["Severe"];
}
