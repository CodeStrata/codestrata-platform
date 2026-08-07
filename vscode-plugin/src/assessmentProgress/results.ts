/** Typed assessment-progress results (Slice 13.6). */

import { DEFAULT_ASSESSMENT_PROGRESS_LIMITATIONS } from "./policy";
import type { AssessmentProgressPhase } from "./phases";

export const ASSESSMENT_PROGRESS_RESULT_STATUSES = [
  "completed",
  "failed",
  "cancelled",
  "unavailable",
] as const;

export type AssessmentProgressResultStatus =
  (typeof ASSESSMENT_PROGRESS_RESULT_STATUSES)[number];

export type AssessmentProgressResult = {
  readonly status: AssessmentProgressResultStatus;
  readonly terminal_phase: AssessmentProgressPhase;
  readonly update_count: number;
  readonly cancellation_supported: true;
  readonly cancellation_requested: boolean;
  readonly primary_result_preserved: true;
  readonly progress_failure_isolated: true;
  readonly limitations: readonly string[];
};

export function createAssessmentProgressResult(
  partial: Omit<
    AssessmentProgressResult,
    | "cancellation_supported"
    | "primary_result_preserved"
    | "progress_failure_isolated"
    | "limitations"
  > & { readonly limitations?: readonly string[] }
): AssessmentProgressResult {
  return {
    ...partial,
    cancellation_supported: true,
    primary_result_preserved: true,
    progress_failure_isolated: true,
    limitations: [
      ...(partial.limitations ?? DEFAULT_ASSESSMENT_PROGRESS_LIMITATIONS),
    ].sort(),
  };
}

export function assessmentProgressResultToStableDict(
  result: AssessmentProgressResult
): Record<string, unknown> {
  return {
    cancellation_requested: result.cancellation_requested,
    cancellation_supported: result.cancellation_supported,
    limitations: [...result.limitations].sort(),
    primary_result_preserved: result.primary_result_preserved,
    progress_failure_isolated: result.progress_failure_isolated,
    status: result.status,
    terminal_phase: result.terminal_phase,
    update_count: result.update_count,
  };
}

export const ASSESSMENT_PROGRESS_ERROR_CATEGORIES = [
  "progress_start_failed",
  "progress_update_failed",
  "progress_completion_failed",
  "progress_cancellation_failed",
  "progress_state_invalid",
  "duplicate_progress_lifecycle",
  "duplicate_terminal_transition",
  "cancellation_race",
  "progress_internal_error",
] as const;

export type AssessmentProgressErrorCategory =
  (typeof ASSESSMENT_PROGRESS_ERROR_CATEGORIES)[number];
