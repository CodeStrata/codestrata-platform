/** Typed HTML report-opening results (Slice 13.7). */

import { DEFAULT_REPORT_OPENING_LIMITATIONS } from "./policy";

export const REPORT_OPENING_RESULT_STATUSES = [
  "available",
  "missing",
  "unsafe_path",
  "invalid_file",
  "ambiguous",
  "stale",
  "opened",
  "open_failed",
  "user_declined",
  "unavailable",
] as const;

export type ReportOpeningResultStatus =
  (typeof REPORT_OPENING_RESULT_STATUSES)[number];

export const REPORT_RECOVERY_CATEGORIES = [
  "rerun_assessment",
  "open_report_manually",
  "inspect_output",
  "select_workspace",
  "none",
] as const;

export type ReportRecoveryCategory =
  (typeof REPORT_RECOVERY_CATEGORIES)[number];

export type ReportOpeningResult = {
  readonly status: ReportOpeningResultStatus;
  readonly report_expected: boolean;
  readonly report_available: boolean;
  readonly open_attempted: boolean;
  readonly open_succeeded: boolean;
  readonly user_action_required: boolean;
  readonly primary_result_preserved: true;
  readonly recovery_category: ReportRecoveryCategory;
  readonly limitations: readonly string[];
};

export function createReportOpeningResult(
  partial: Omit<
    ReportOpeningResult,
    "primary_result_preserved" | "limitations"
  > & { readonly limitations?: readonly string[] }
): ReportOpeningResult {
  return {
    ...partial,
    primary_result_preserved: true,
    limitations: [
      ...(partial.limitations ?? DEFAULT_REPORT_OPENING_LIMITATIONS),
    ].sort(),
  };
}

export function reportOpeningResultToStableDict(
  result: ReportOpeningResult
): Record<string, unknown> {
  return {
    limitations: [...result.limitations].sort(),
    open_attempted: result.open_attempted,
    open_succeeded: result.open_succeeded,
    primary_result_preserved: result.primary_result_preserved,
    recovery_category: result.recovery_category,
    report_available: result.report_available,
    report_expected: result.report_expected,
    status: result.status,
    user_action_required: result.user_action_required,
  };
}

export const REPORT_ERROR_CATEGORIES = [
  "report_not_found",
  "report_path_unsafe",
  "report_not_regular_file",
  "report_type_invalid",
  "report_ambiguous",
  "report_stale",
  "report_open_failed",
  "report_disappeared",
  "workspace_unavailable",
  "report_internal_error",
] as const;

export type ReportErrorCategory = (typeof REPORT_ERROR_CATEGORIES)[number];
