import React, { useState } from "react";
import { m, AnimatePresence } from "motion/react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { smoothEase } from "../lib/motion";

export interface MathDrawerProps {
  title: string;
  initialExpanded?: boolean;
  children: React.ReactNode;
  className?: string;
}

export const MathDrawer: React.FC<MathDrawerProps> = ({
  title,
  initialExpanded = false,
  children,
  className = "",
}) => {
  const [isOpen, setIsOpen] = useState<boolean>(initialExpanded);

  return (
    <div
      className={`border border-[var(--border-subtle)] rounded-xl p-3 bg-[var(--bg-elevated)] transition-colors ${className}`}
    >
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        aria-expanded={isOpen}
        className="min-h-[44px] text-xs font-bold text-teal-700 dark:text-teal-400 hover:text-teal-900 dark:hover:text-teal-300 flex items-center justify-between w-full text-left focus:outline-none focus:ring-2 focus:ring-teal-500 rounded px-1 transition-colors"
      >
        <span className="flex items-center gap-1.5">
          <span aria-hidden="true">📐</span>
          <span>{title}</span>
        </span>
        <span className="flex items-center gap-1 text-[11px] font-semibold text-gray-500 dark:text-gray-400">
          <span>{isOpen ? "Hide Math" : "Expand Math"}</span>
          {isOpen ? (
            <ChevronUp className="w-4 h-4" strokeWidth={1.75} aria-hidden="true" />
          ) : (
            <ChevronDown className="w-4 h-4" strokeWidth={1.75} aria-hidden="true" />
          )}
        </span>
      </button>

      <AnimatePresence initial={false}>
        {isOpen && (
          <m.div
            key="content"
            initial={{ opacity: 0, y: -6, height: 0 }}
            animate={{ opacity: 1, y: 0, height: "auto" }}
            exit={{ opacity: 0, y: -6, height: 0 }}
            transition={smoothEase}
            className="overflow-hidden"
          >
            <div className="mt-3 text-xs text-[var(--text-secondary)] space-y-3 border-t border-[var(--border-subtle)] pt-3 font-mono tabular-nums leading-relaxed">
              {children}
            </div>
          </m.div>
        )}
      </AnimatePresence>
    </div>
  );
};
