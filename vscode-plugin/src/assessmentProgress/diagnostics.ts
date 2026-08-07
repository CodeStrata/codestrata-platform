/** Privacy-safe assessment-progress diagnostics (Slice 13.6). */

import { ASSESSMENT_PROGRESS_POLICY_VERSION } from "./policy";
import type { AssessmentProgressPhase } from "./phases";
import type { AssessmentProgressResultStatus } from "./results";

export type AssessmentProgressDiagnostics = {
  readonly progress_policy_version: typeof ASSESSMENT_PROGRESS_POLICY_VERSION;
  readonly operation: "run_assessment" | "run_assessment_with_ai";
  readonly ai_requested: boolean;
  readonly progress_started: boolean;
  readonly progress_closed: boolean;
  readonly terminal_phase: AssessmentProgressPhase | "not_started";
  readonly update_count: number;
  readonly cancellation_supported: true;
  readonly cancellation_requested: boolean;
  readonly cancellation_result_category: "none" | "user_cancelled";
  readonly primary_result_preserved: true;
  readonly telemetry_failure_isolated: true;
  readonly analytics_failure_isolated: true;
  readonly progress_failure_isolated: true;
  readonly terminal_status: AssessmentProgressResultStatus | "in_progress";
  readonly limitation_codes: readonly string[];
};

export function assessmentProgressDiagnosticsToStableDict(
  diag: AssessmentProgressDiagnostics
): Record<string, unknown> {
  return {
    ai_requested: diag.ai_requested,
    analytics_failure_isolated: diag.analytics_failure_isolated,
    cancellation_requested: diag.cancellation_requested,
    cancellation_result_category: diag.cancellation_result_category,
    cancellation_supported: diag.cancellation_supported,
    limitation_codes: [...diag.limitation_codes].sort(),
    operation: diag.operation,
    primary_result_preserved: diag.primary_result_preserved,
    progress_closed: diag.progress_closed,
    progress_failure_isolated: diag.progress_failure_isolated,
    progress_policy_version: diag.progress_policy_version,
    progress_started: diag.progress_started,
    telemetry_failure_isolated: diag.telemetry_failure_isolated,
    terminal_phase: diag.terminal_phase,
    terminal_status: diag.terminal_status,
    update_count: diag.update_count,
  };
}

const FORBIDDEN_KEYS = [
  "workspace_path",
  "repository_path",
  "report_path",
  "cli_path",
  "stdout",
  "stderr",
  "environment",
  "source",
  "findings",
  "provider",
  "model",
  "credentials",
  "elapsed_ms",
  "timestamp",
] as const;

export function progressDiagnosticsContainForbiddenKeys(
  blob: Record<string, unknown>
): string[] {
  const hits: string[] = [];
  for (const key of FORBIDDEN_KEYS) {
    if (key in blob) {
      hits.push(key);
    }
  }
  const text = JSON.stringify(blob);
  if (
    text.includes("/Users/") ||
    text.includes("/home/") ||
    text.includes("C:\\\\")
  ) {
    hits.push("absolute_path_value");
  }
  return hits;
}
