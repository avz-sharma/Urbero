import React, { useState, useEffect } from "react";
import { m, AnimatePresence } from "motion/react";
import { Copy, Check } from "lucide-react";

export interface CopyButtonProps {
  textToCopy: string;
  defaultLabel: string;
  copiedLabel?: string;
  className?: string;
}

export const CopyButton: React.FC<CopyButtonProps> = ({
  textToCopy,
  defaultLabel,
  copiedLabel = "✓ Copied to Clipboard!",
  className = "",
}) => {
  const [copied, setCopied] = useState<boolean>(false);

  useEffect(() => {
    if (!copied) return;
    const timer = setTimeout(() => setCopied(false), 1800);
    return () => clearTimeout(timer);
  }, [copied]);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(textToCopy);
      setCopied(true);
    } catch {
      // Fallback if clipboard API is restricted
    }
  };

  return (
    <button
      type="button"
      onClick={handleCopy}
      className={`min-h-[44px] px-4 py-2 text-xs font-bold rounded-lg transition-all shadow-sm focus:outline-none focus:ring-2 focus:ring-teal-500 inline-flex items-center justify-center gap-2 ${
        copied
          ? "bg-teal-700 text-white dark:bg-teal-600"
          : "bg-teal-600 text-white hover:bg-teal-700 dark:bg-teal-500 dark:text-gray-950 dark:hover:bg-teal-400"
      } ${className}`}
      aria-label={copied ? copiedLabel : defaultLabel}
    >
      <AnimatePresence mode="wait" initial={false}>
        {copied ? (
          <m.span
            key="check"
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.8, opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="inline-flex items-center gap-1.5"
          >
            <Check className="w-4 h-4" strokeWidth={2} aria-hidden="true" />
            <span>{copiedLabel}</span>
          </m.span>
        ) : (
          <m.span
            key="copy"
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.8, opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="inline-flex items-center gap-1.5"
          >
            <Copy className="w-4 h-4" strokeWidth={1.75} aria-hidden="true" />
            <span>{defaultLabel}</span>
          </m.span>
        )}
      </AnimatePresence>
    </button>
  );
};
