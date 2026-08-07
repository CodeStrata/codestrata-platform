/**
 * Closed assessment-progress phase vocabulary (Slice 13.6).
 *
 * Only phases the extension can truthfully observe without Engine structured
 * progress signals. No fabricated scanning/AI/recommendation phases.
 */

export const ASSESSMENT_PROGRESS_PHASES = [
  "running_assessment",
  "finalizing",
  "locating_report",
  "completed",
  "failed",
  "cancelled",
] as const;

export type AssessmentProgressPhase =
  (typeof ASSESSMENT_PROGRESS_PHASES)[number];

export function isAssessmentProgressPhase(
  value: string
): value is AssessmentProgressPhase {
  return (ASSESSMENT_PROGRESS_PHASES as readonly string[]).includes(value);
}

export const TERMINAL_PROGRESS_PHASES: readonly AssessmentProgressPhase[] = [
  "completed",
  "failed",
  "cancelled",
] as const;

export function isTerminalProgressPhase(
  phase: AssessmentProgressPhase
): boolean {
  return (TERMINAL_PROGRESS_PHASES as readonly string[]).includes(phase);
}

/** Allowed phase transitions (visible lifecycle only). */
export const ALLOWED_PROGRESS_TRANSITIONS: Readonly<
  Record<AssessmentProgressPhase, readonly AssessmentProgressPhase[]>
> = {
  running_assessment: ["finalizing", "locating_report", "failed", "cancelled"],
  finalizing: ["locating_report", "completed", "failed", "cancelled"],
  locating_report: ["completed", "failed", "cancelled"],
  completed: [],
  failed: [],
  cancelled: [],
};

export function canTransitionProgress(
  from: AssessmentProgressPhase,
  to: AssessmentProgressPhase
): boolean {
  return ALLOWED_PROGRESS_TRANSITIONS[from].includes(to);
}

/** Bounded, privacy-safe progress message text (no paths, models, or findings). */
export function progressMessageForPhase(
  phase: AssessmentProgressPhase,
  aiRequested: boolean
): string {
  switch (phase) {
    case "running_assessment":
      return aiRequested
        ? "Running CodeStrata assessment with AI…"
        : "Running CodeStrata assessment…";
    case "finalizing":
      return "Finalizing assessment…";
    case "locating_report":
      return "Locating generated report…";
    case "completed":
      return "Assessment complete";
    case "failed":
      return "Assessment failed";
    case "cancelled":
      return "Assessment cancelled";
    default:
      return "Running CodeStrata assessment…";
  }
}

export function progressTitle(aiRequested: boolean): string {
  return aiRequested
    ? "CodeStrata Engineering Assessment (optional AI)…"
    : "CodeStrata Engineering Assessment…";
}
