/** Typed assessment-execution results (Slice 13.5). */

import { DEFAULT_ASSESSMENT_EXECUTION_LIMITATIONS } from "./policy";

export const ASSESSMENT_EXECUTION_RESULT_STATUSES = [
  "success",
  "failure",
  "cancelled",
  "workspace_unavailable",
  "repository_not_initialized",
  "invalid_repository_configuration",
  "partial_repository_configuration",
  "cli_unavailable",
  "cli_incompatible",
  "invocation_failed",
  "report_missing",
] as const;

export type AssessmentExecutionResultStatus =
  (typeof ASSESSMENT_EXECUTION_RESULT_STATUSES)[number];

export const ASSESSMENT_PRIMARY_EXIT_CATEGORIES = [
  "success",
  "failure",
  "cancelled",
  "timed_out",
  "process_start_failed",
  "unavailable",
] as const;

export type AssessmentPrimaryExitCategory =
  (typeof ASSESSMENT_PRIMARY_EXIT_CATEGORIES)[number];

export const ASSESSMENT_RECOVERY_CATEGORIES = [
  "initialize_repository",
  "inspect_configuration",
  "install_cli",
  "correct_cli_setting",
  "retry_assessment",
  "review_cli_output",
  "open_report_manually",
  "none",
] as const;

export type AssessmentRecoveryCategory =
  (typeof ASSESSMENT_RECOVERY_CATEGORIES)[number];

export const ASSESSMENT_CONSENT_CATEGORIES = [
  "allowed_for_session",
  "denied",
  "suppressed_non_interactive",
  "not_reached",
] as const;

export type AssessmentConsentCategory =
  (typeof ASSESSMENT_CONSENT_CATEGORIES)[number];

export type AssessmentExecutionResult = {
  readonly operation: "run_assessment" | "run_assessment_with_ai";
  readonly status: AssessmentExecutionResultStatus;
  readonly ai_requested: boolean;
  readonly primary_exit_category: AssessmentPrimaryExitCategory;
  readonly product_invocation_count: number;
  readonly consent_category: AssessmentConsentCategory;
  readonly telemetry_isolated: true;
  readonly analytics_isolated: true;
  readonly report_expected: boolean;
  readonly report_available: boolean;
  readonly cancellation_category: "none" | "user_cancelled";
  readonly recovery_category: AssessmentRecoveryCategory;
  readonly limitations: readonly string[];
};

export function createAssessmentExecutionResult(
  partial: Omit<
    AssessmentExecutionResult,
    "telemetry_isolated" | "analytics_isolated" | "limitations"
  > & { readonly limitations?: readonly string[] }
): AssessmentExecutionResult {
  return {
    ...partial,
    telemetry_isolated: true,
    analytics_isolated: true,
    limitations: [
      ...(partial.limitations ?? DEFAULT_ASSESSMENT_EXECUTION_LIMITATIONS),
    ].sort(),
  };
}

export function assessmentExecutionResultToStableDict(
  result: AssessmentExecutionResult
): Record<string, unknown> {
  return {
    ai_requested: result.ai_requested,
    analytics_isolated: result.analytics_isolated,
    cancellation_category: result.cancellation_category,
    consent_category: result.consent_category,
    limitations: [...result.limitations].sort(),
    operation: result.operation,
    primary_exit_category: result.primary_exit_category,
    product_invocation_count: result.product_invocation_count,
    recovery_category: result.recovery_category,
    report_available: result.report_available,
    report_expected: result.report_expected,
    status: result.status,
    telemetry_isolated: result.telemetry_isolated,
  };
}

export const ASSESSMENT_ERROR_CATEGORIES = [
  "workspace_unavailable",
  "repository_not_initialized",
  "repository_configuration_invalid",
  "cli_unavailable",
  "cli_incompatible",
  "consent_failure_isolated",
  "process_start_failed",
  "assessment_failed",
  "assessment_cancelled",
  "assessment_timed_out",
  "report_missing",
  "telemetry_failure_isolated",
  "analytics_failure_isolated",
  "internal_assessment_error",
] as const;

export type AssessmentErrorCategory = (typeof ASSESSMENT_ERROR_CATEGORIES)[number];
