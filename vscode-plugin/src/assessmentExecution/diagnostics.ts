/** Privacy-safe assessment-execution diagnostics (Slice 13.5). */

import { ASSESSMENT_EXECUTION_POLICY_VERSION } from "./policy";
import type {
  AssessmentConsentCategory,
  AssessmentExecutionResultStatus,
  AssessmentPrimaryExitCategory,
} from "./results";

export type AssessmentExecutionDiagnostics = {
  readonly assessment_policy_version: typeof ASSESSMENT_EXECUTION_POLICY_VERSION;
  readonly operation: "run_assessment" | "run_assessment_with_ai";
  readonly ai_requested: boolean;
  readonly readiness_passed: boolean;
  readonly consent_category: AssessmentConsentCategory;
  readonly product_invocation_count: number;
  readonly primary_exit_category: AssessmentPrimaryExitCategory;
  readonly cancelled: boolean;
  readonly report_expected: boolean;
  readonly report_available: boolean;
  readonly telemetry_failure_isolated: true;
  readonly analytics_failure_isolated: true;
  readonly source_mutation_detected: false;
  readonly configuration_mutation_detected: false;
  readonly git_mutation_detected: false;
  readonly terminal_status: AssessmentExecutionResultStatus;
  readonly limitation_codes: readonly string[];
};

export function assessmentExecutionDiagnosticsToStableDict(
  diag: AssessmentExecutionDiagnostics
): Record<string, unknown> {
  return {
    ai_requested: diag.ai_requested,
    analytics_failure_isolated: diag.analytics_failure_isolated,
    assessment_policy_version: diag.assessment_policy_version,
    cancelled: diag.cancelled,
    configuration_mutation_detected: diag.configuration_mutation_detected,
    consent_category: diag.consent_category,
    git_mutation_detected: diag.git_mutation_detected,
    limitation_codes: [...diag.limitation_codes].sort(),
    operation: diag.operation,
    primary_exit_category: diag.primary_exit_category,
    product_invocation_count: diag.product_invocation_count,
    readiness_passed: diag.readiness_passed,
    report_available: diag.report_available,
    report_expected: diag.report_expected,
    source_mutation_detected: diag.source_mutation_detected,
    telemetry_failure_isolated: diag.telemetry_failure_isolated,
    terminal_status: diag.terminal_status,
  };
}

const FORBIDDEN_KEYS = [
  "workspace_path",
  "repository_path",
  "report_path",
  "cli_path",
  "executable_path",
  "stdout",
  "stderr",
  "environment",
  "source",
  "findings",
  "evidence",
  "credentials",
  "provider",
  "model",
] as const;

export function assessmentDiagnosticsContainForbiddenKeys(
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
