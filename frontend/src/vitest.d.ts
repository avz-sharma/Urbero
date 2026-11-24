import "vitest";

declare module "vitest" {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  interface Matchers<R = void, T = unknown> {
    toHaveNoViolations(): R;
  }
}
