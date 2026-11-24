import type { Transition } from "motion/react";

export const snappySpring: Transition = {
  type: "spring",
  stiffness: 420,
  damping: 32,
  mass: 0.8,
};

export const smoothEase: Transition = {
  duration: 0.26,
  ease: [0.22, 1, 0.36, 1],
};
