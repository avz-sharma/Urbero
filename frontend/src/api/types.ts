/**
 * Type narrowing layer over openapi-typescript generated schemas.
 * Never hand-duplicate API schemas; derive strictly from openapi-typescript.
 */

import type { components } from "./generated";

export type DailyPlanResponse = components["schemas"]["DailyPlanResponse"];
export type DailyPlanRequest = components["schemas"]["DailyPlanRequest"];
export type CPCBAQIResult = components["schemas"]["CPCBAQIResult"];
export type SubIndexItem = components["schemas"]["SubIndexItem"];
export type ConfidenceResult = components["schemas"]["ConfidenceResult"];
export type CommuteModeComparison = components["schemas"]["CommuteModeComparison"];
export type RoomCADRResult = components["schemas"]["RoomCADRResult"];
export type RoomDimensions = components["schemas"]["RoomDimensions"];
export type RoomIndoorFactors = components["schemas"]["RoomIndoorFactors"];
export type MergedErrandsResult = components["schemas"]["MergedErrandsResult"];
export type ErrandStop = components["schemas"]["ErrandStop"];
export type ScheduledActivity = components["schemas"]["ScheduledActivity"];
export type OptimizedActivity = components["schemas"]["OptimizedActivity"];
export type RoutineOptimizationResult = components["schemas"]["RoutineOptimizationResult"];
export type WhatsAppFamilyCard = components["schemas"]["WhatsAppFamilyCard"];
export type CommunityBrief = components["schemas"]["CommunityBrief"];
export type RecommendationCard = components["schemas"]["RecommendationCard"];
export type StationMetadataSchema = components["schemas"]["StationMetadataSchema"];
export type MathBreakdownSchema = components["schemas"]["MathBreakdownSchema"];
export type LocationSearchResult = components["schemas"]["LocationSearchResult"];
export type ReverseGeocodeResult = components["schemas"]["ReverseGeocodeResult"];

export type ActiveLocation = {
  label: string;
  lat: number;
  lon: number;
  origin: "gps" | "search" | "preset";
};

