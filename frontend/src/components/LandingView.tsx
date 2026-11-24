import React from "react";
import { ArrowRight, ShieldCheck, Activity, Wind, Sparkles } from "lucide-react";
import { Ripple } from "./ui/Ripple";
import { PulsatingButton } from "./ui/PulsatingButton";

export interface LandingViewProps {
  onGetStarted: () => void;
}

export const LandingView: React.FC<LandingViewProps> = ({ onGetStarted }) => {
  return (
    <div className="relative min-h-[calc(100vh-4rem)] flex flex-col items-center justify-center overflow-hidden text-center px-6 py-12">
      {/* Concentric Ripple centered in the middle of the homepage and evenly spread */}
      <Ripple
        mainCircleSize={260}
        mainCircleOpacity={0.24}
        numCircles={10}
      />

      <div className="relative z-10 flex flex-col items-center max-w-4xl mx-auto">
        {/* Civic-Health Badge Pill */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-xs font-semibold text-teal-800 dark:text-teal-300 mb-6 shadow-2xs">
          <Sparkles className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" strokeWidth={1.75} aria-hidden="true" />
          <span>Next-Gen Urban Air Quality & Household Exposure Assistant</span>
        </div>

        {/* Hero Display Typography */}
        <h1 className="relative z-10 text-7xl sm:text-8xl md:text-9xl font-extrabold tracking-tight leading-none select-none">
          <span className="urbero-wordmark">Urbero</span>
        </h1>

        {/* Tagline Subtitle */}
        <p className="relative z-10 text-base sm:text-lg md:text-xl text-[var(--text-secondary)] max-w-2xl mt-6 leading-relaxed">
          Deterministic Urban Air Quality & Household Exposure Assistant for Indian Cities — Real CPCB Math, Zero Fabricated Data.
        </p>

        {/* Primary CTA: Pulsating Get Started Button */}
        <div className="relative z-10 mt-9">
          <PulsatingButton
            type="button"
            onClick={onGetStarted}
            className="min-h-[52px] px-9 rounded-full font-semibold text-sm sm:text-base bg-[#0F766E] hover:bg-[#115E59] text-white dark:bg-[#2DD4BF] dark:hover:bg-[#5EEAD4] dark:text-[#042F2E] shadow-lg transition-all hover:scale-[1.02] active:scale-[0.98] focus:outline-none focus:ring-4 focus:ring-teal-500/40 inline-flex items-center justify-center cursor-pointer"
            duration="2s"
          >
            <span className="inline-flex items-center gap-3">
              <span>Get Started</span>
              <ArrowRight className="w-5 h-5" strokeWidth={2} aria-hidden="true" />
            </span>
          </PulsatingButton>
        </div>

        {/* 3 Pillar Feature Badges */}
        <div className="relative z-10 mt-14 grid grid-cols-1 sm:grid-cols-3 gap-3 w-full max-w-3xl">
          <div className="p-3.5 rounded-xl bg-[var(--bg-surface)]/80 backdrop-blur-sm border border-[var(--border-subtle)] text-left flex items-start gap-3 shadow-2xs">
            <div className="p-2 rounded-lg bg-teal-50 dark:bg-teal-950 text-teal-700 dark:text-teal-400 shrink-0">
              <Activity className="w-4 h-4" strokeWidth={1.75} aria-hidden="true" />
            </div>
            <div>
              <div className="text-xs font-bold text-[var(--text-primary)]">
                CPCB Breakpoint Estimates
              </div>
              <div className="text-[11px] text-[var(--text-secondary)] mt-0.5">
                Labelled station and model data with pollutant validity checks
              </div>
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-[var(--bg-surface)]/80 backdrop-blur-sm border border-[var(--border-subtle)] text-left flex items-start gap-3 shadow-2xs">
            <div className="p-2 rounded-lg bg-teal-50 dark:bg-teal-950 text-teal-700 dark:text-teal-400 shrink-0">
              <ShieldCheck className="w-4 h-4" strokeWidth={1.75} aria-hidden="true" />
            </div>
            <div>
              <div className="text-xs font-bold text-[var(--text-primary)]">
                Planet vs. Lungs
              </div>
              <div className="text-[11px] text-[var(--text-secondary)] mt-0.5">
                Personal PM2.5 dose compared with tailpipe CO₂
              </div>
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-[var(--bg-surface)]/80 backdrop-blur-sm border border-[var(--border-subtle)] text-left flex items-start gap-3 shadow-2xs">
            <div className="p-2 rounded-lg bg-teal-50 dark:bg-teal-950 text-teal-700 dark:text-teal-400 shrink-0">
              <Wind className="w-4 h-4" strokeWidth={1.75} aria-hidden="true" />
            </div>
            <div>
              <div className="text-xs font-bold text-[var(--text-primary)]">
                Room CADR Sizing
              </div>
              <div className="text-[11px] text-[var(--text-secondary)] mt-0.5">
                Deterministic air changes per hour & sealing guidance
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LandingView;
