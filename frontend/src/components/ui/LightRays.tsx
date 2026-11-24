import React, { type CSSProperties, type HTMLAttributes } from "react";
import { m, useReducedMotion } from "motion/react";

export interface LightRaysProps extends HTMLAttributes<HTMLDivElement> {
  count?: number;
  color?: string;
  className?: string;
  style?: CSSProperties;
}

interface RayItem {
  id: number;
  leftPercent: number;
  angle: number;
  widthPx: number;
  heightVh: number;
  opacity: number;
  duration: number;
  delay: number;
}

const STATIC_RAYS: RayItem[] = [
  { id: 1, leftPercent: 12, angle: -18, widthPx: 120, heightVh: 110, opacity: 0.65, duration: 8.5, delay: 0 },
  { id: 2, leftPercent: 28, angle: -8, widthPx: 160, heightVh: 125, opacity: 0.9, duration: 9.5, delay: 1.2 },
  { id: 3, leftPercent: 44, angle: 2, widthPx: 210, heightVh: 130, opacity: 1.0, duration: 11, delay: 0.5 },
  { id: 4, leftPercent: 58, angle: 10, widthPx: 180, heightVh: 120, opacity: 0.85, duration: 10, delay: 2.1 },
  { id: 5, leftPercent: 72, angle: 18, widthPx: 140, heightVh: 115, opacity: 0.7, duration: 8.8, delay: 1.5 },
  { id: 6, leftPercent: 86, angle: 26, widthPx: 110, heightVh: 105, opacity: 0.55, duration: 9.2, delay: 0.8 },
  { id: 7, leftPercent: 35, angle: -4, widthPx: 190, heightVh: 125, opacity: 0.75, duration: 12, delay: 2.7 },
];

export const LightRays: React.FC<LightRaysProps> = ({
  count = 7,
  color,
  className = "",
  style,
  ...props
}) => {
  const prefersReduced = useReducedMotion();
  const effectiveCount = prefersReduced ? 0 : Math.min(count, STATIC_RAYS.length);
  const activeRays = STATIC_RAYS.slice(0, effectiveCount);

  // Fallback default colors if not supplied:
  // Light mode soft civic teal; Dark mode luminous cyan-teal
  const rayColor = color || "var(--ray-color, rgba(15, 118, 110, 0.14))";

  return (
    <div
      aria-hidden="true"
      className={`fixed inset-0 z-0 pointer-events-none overflow-hidden select-none ${className}`}
      style={style}
      {...props}
    >
      {/* Top ambient focal glow */}
      <div
        className="absolute -top-32 left-1/2 -translate-x-1/2 w-[85vw] max-w-5xl h-72 rounded-full blur-3xl opacity-60 dark:opacity-45 mix-blend-multiply dark:mix-blend-screen pointer-events-none"
        style={{
          background: `radial-gradient(circle at center, ${rayColor} 0%, transparent 70%)`,
        }}
      />

      {/* Atmospheric light beams */}
      {activeRays.map((ray) => (
        <m.div
          key={ray.id}
          className="absolute -top-20 origin-top mix-blend-multiply dark:mix-blend-screen pointer-events-none"
          style={{
            left: `${ray.leftPercent}%`,
            width: `${ray.widthPx}px`,
            height: `${ray.heightVh}vh`,
            background: `linear-gradient(180deg, ${rayColor} 0%, rgba(45, 212, 191, 0.04) 55%, transparent 100%)`,
            filter: "blur(28px)",
            transform: `rotate(${ray.angle}deg)`,
          }}
          animate={
            prefersReduced
              ? undefined
              : {
                  opacity: [ray.opacity * 0.7, ray.opacity, ray.opacity * 0.7],
                  transform: [
                    `rotate(${ray.angle - 1.5}deg) scaleX(0.95)`,
                    `rotate(${ray.angle + 1.5}deg) scaleX(1.05)`,
                    `rotate(${ray.angle - 1.5}deg) scaleX(0.95)`,
                  ],
                }
          }
          transition={
            prefersReduced
              ? undefined
              : {
                  duration: ray.duration,
                  delay: ray.delay,
                  repeat: Infinity,
                  ease: "easeInOut",
                }
          }
        />
      ))}
    </div>
  );
};

export default LightRays;
