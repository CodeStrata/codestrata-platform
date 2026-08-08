import type { Completeness } from "../metrics/metricResult";

export type UiStateKind =
  | "loading"
  | "zero"
  | "partial"
  | "unavailable"
  | "not_applicable"
  | "error";

export function stateFromCompleteness(
  completeness: Completeness,
  value: number | null,
  status: string,
): UiStateKind {
  if (status === "error" || completeness === "unavailable") {
    return "unavailable";
  }
  if (completeness === "not_applicable") {
    return "not_applicable";
  }
  if (completeness === "partial") {
    return "partial";
  }
  if (value === 0) {
    return "zero";
  }
  return "zero"; // callers should pass loading separately
}

export function isUnavailableNotZero(kind: UiStateKind): boolean {
  return kind === "unavailable" || kind === "error" || kind === "not_applicable";
}
