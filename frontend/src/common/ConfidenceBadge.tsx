import React from "react";
import type { ConfidenceResult } from "../api/types";
import { ShieldCheck, AlertCircle, AlertTriangle } from "lucide-react";

export interface ConfidenceBadgeProps {
  confidence: Pick<ConfidenceResult, "level" | "reason"> &
    Partial<Pick<ConfidenceResult, "score_percent">>;
  showScore?: boolean;
  className?: string;
  showReason?: boolean;
}

export const ConfidenceBadge: React.FC<ConfidenceBadgeProps> = ({
  confidence,
  showScore = true,
  className = "",
  showReason = false,
}) => {
  const level = confidence.level.toLowerCase();

  let Icon = ShieldCheck;
  let colorClasses =
    "bg-[#ECFDF5] text-[#065F46] border-[#A7F3D0] dark:bg-[#052E24] dark:text-[#6EE7B7] dark:border-[#065F46]";

  if (level === "medium") {
    Icon = AlertCircle;
    colorClasses =
      "bg-[#FFFBEB] text-[#92400E] border-[#FDE68A] dark:bg-[#2E1E05] dark:text-[#FCD34D] dark:border-[#92400E]";
  } else if (level === "low") {
    Icon = AlertTriangle;
    colorClasses =
      "bg-[#FEF2F2] text-[#991B1B] border-[#FCA5A5] dark:bg-[#310B0E] dark:text-[#FCA5A5] dark:border-[#991B1B]";
  }

  return (
    <div className="flex flex-col gap-1">
      <div
        className={`inline-flex items-center gap-1.5 px-3 py-1 text-xs font-bold rounded-full border shadow-2xs ${colorClasses} ${className}`}
        title={confidence.reason}
        aria-label={`Data Confidence: ${confidence.level}${confidence.score_percent === undefined ? "" : ` (${confidence.score_percent}%)`} - ${confidence.reason}`}
      >
        <Icon
          className="w-3.5 h-3.5 shrink-0"
          strokeWidth={1.75}
          aria-hidden="true"
        />
        <span>
          Data Confidence: {confidence.level}
          {showScore && confidence.score_percent !== undefined && (
            <span className="tabular-nums font-semibold ml-1">
              ({confidence.score_percent}%)
            </span>
          )}
        </span>
      </div>
      {showReason && (
        <span className="text-[11px] text-gray-500 dark:text-gray-400 pl-1">
          {confidence.reason}
        </span>
      )}
    </div>
  );
};
