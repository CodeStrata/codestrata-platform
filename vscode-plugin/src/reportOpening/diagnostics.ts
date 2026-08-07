/** Privacy-safe report-opening diagnostics (Slice 13.7). */

import { REPORT_OPENING_POLICY_VERSION } from "./policy";
import type { ReportOpeningResultStatus } from "./results";

export type ReportOpeningDiagnostics = {
  readonly report_policy_version: typeof REPORT_OPENING_POLICY_VERSION;
  readonly operation: "open_report" | "post_assessment_report";
  readonly primary_result_category: string;
  readonly report_expected: boolean;
  readonly report_available: boolean;
  readonly containment_valid: boolean;
  readonly file_valid: boolean;
  readonly open_attempted: boolean;
  readonly open_succeeded: boolean;
  readonly user_action_required: boolean;
  readonly primary_result_preserved: true;
  readonly telemetry_invoked: false;
  readonly analytics_invoked: false;
  readonly terminal_status: ReportOpeningResultStatus;
  readonly limitation_codes: readonly string[];
};

export function reportOpeningDiagnosticsToStableDict(
  diag: ReportOpeningDiagnostics
): Record<string, unknown> {
  return {
    analytics_invoked: diag.analytics_invoked,
    containment_valid: diag.containment_valid,
    file_valid: diag.file_valid,
    limitation_codes: [...diag.limitation_codes].sort(),
    open_attempted: diag.open_attempted,
    open_succeeded: diag.open_succeeded,
    operation: diag.operation,
    primary_result_category: diag.primary_result_category,
    primary_result_preserved: diag.primary_result_preserved,
    report_available: diag.report_available,
    report_expected: diag.report_expected,
    report_policy_version: diag.report_policy_version,
    telemetry_invoked: diag.telemetry_invoked,
    terminal_status: diag.terminal_status,
    user_action_required: diag.user_action_required,
  };
}

const FORBIDDEN_KEYS = [
  "report_path",
  "workspace_path",
  "uri",
  "html",
  "file_contents",
  "stdout",
  "stderr",
  "environment",
  "source",
  "findings",
  "evidence",
  "credentials",
  "mtime",
  "timestamp",
] as const;

export function reportDiagnosticsContainForbiddenKeys(
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
    text.includes("C:\\\\") ||
    text.includes("file:")
  ) {
    hits.push("absolute_path_or_uri_value");
  }
  return hits;
}
