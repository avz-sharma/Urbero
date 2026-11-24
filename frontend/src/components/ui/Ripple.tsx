import React, { type CSSProperties } from "react";
import { cn } from "@/lib/utils";

export interface RippleProps {
  mainCircleSize?: number;
  mainCircleOpacity?: number;
  numCircles?: number;
  className?: string;
  style?: CSSProperties;
}

export const Ripple = React.memo<RippleProps>(function Ripple({
  mainCircleSize = 260,
  mainCircleOpacity = 0.24,
  numCircles = 10,
  className,
  style,
}) {
  return (
    <div
      aria-hidden="true"
      className={cn(
        "pointer-events-none absolute inset-0 select-none overflow-hidden",
        className
      )}
      style={style}
    >
      {Array.from({ length: numCircles }).map((_, i) => {
        const size = mainCircleSize + i * 110;
        const opacity = Math.max(mainCircleOpacity - i * 0.02, 0.03);
        const animationDelay = `${i * 0.18}s`;

        return (
          <div
            key={i}
            className="absolute rounded-full border border-teal-600/25 dark:border-teal-400/25 bg-[var(--foreground)]/5 shadow-2xs animate-ripple motion-reduce:animate-none"
            style={
              {
                width: `${size}px`,
                height: `${size}px`,
                opacity: opacity,
                animationDelay: animationDelay,
                top: "50%",
                left: "50%",
                transform: "translate(-50%, -50%) scale(1)",
                "--i": i,
                "--duration": "3.6s",
              } as CSSProperties
            }
          />
        );
      })}
    </div>
  );
});

Ripple.displayName = "Ripple";

export default Ripple;
