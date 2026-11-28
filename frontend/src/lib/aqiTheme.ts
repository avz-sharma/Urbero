import {
  ShieldCheck,
  Wind,
  AlertCircle,
  AlertTriangle,
  OctagonAlert,
  Siren,
} from "lucide-react";

const bands = new Map([
  ["good", { icon: ShieldCheck, textColor: "#065F46" }],
  ["satisfactory", { icon: Wind, textColor: "#3F6212" }],
  ["moderate", { icon: AlertCircle, textColor: "#92400E" }],
  ["poor", { icon: AlertTriangle, textColor: "#9A3412" }],
  ["very poor", { icon: OctagonAlert, textColor: "#991B1B" }],
  ["severe", { icon: Siren, textColor: "#6B21A8" }],
]);
const unknownBand = { icon: AlertCircle, textColor: "#475A5E" };

export function getAQIBand(category: string) {
  return bands.get(category.trim().toLowerCase()) ?? unknownBand;
}
