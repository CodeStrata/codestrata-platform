/** Privacy-safe workflow diagnostics (no paths / args / stdout). */

import type { TelemetryDecisionCategory } from "./context";
import type { WorkflowOperation } from "./operations";
import type { WorkflowResultStatus } from "./results";
import type { WorkflowState } from "./states";
import { WORKFLOW_POLICY_VERSION } from "./policy";

export type WorkflowDiagnostics = {
  readonly workflow_policy_version: typeof WORKFLOW_POLICY_VERSION;
  readonly operation: WorkflowOperation;
  readonly current_state: WorkflowState;
  readonly terminal_status: WorkflowResultStatus | "in_progress";
  readonly transition_count: number;
  /** Product operation CLI invocations (init/assess) — excludes version probes. */
  readonly cli_invocation_count: number;
  /** Side-effect-free discovery probes for this command. */
  readonly discovery_probe_count: number;
  readonly discovery_status: string;
  readonly progress_started: boolean;
  readonly progress_closed: boolean;
  readonly report_available: boolean;
  readonly report_opened: boolean;
  readonly telemetry_decision_category: TelemetryDecisionCategory;
  readonly telemetry_failure_isolated: boolean;
  readonly analytics_failure_isolated: boolean;
  readonly primary_result_preserved: boolean;
  readonly limitation_codes: readonly string[];
};

export function workflowDiagnosticsToStableDict(
  diag: WorkflowDiagnostics
): Record<string, unknown> {
  return {
    analytics_failure_isolated: diag.analytics_failure_isolated,
    cli_invocation_count: diag.cli_invocation_count,
    current_state: diag.current_state,
    discovery_probe_count: diag.discovery_probe_count,
    discovery_status: diag.discovery_status,
    limitation_codes: [...diag.limitation_codes].sort(),
    operation: diag.operation,
    primary_result_preserved: diag.primary_result_preserved,
    progress_closed: diag.progress_closed,
    progress_started: diag.progress_started,
    report_available: diag.report_available,
    report_opened: diag.report_opened,
    telemetry_decision_category: diag.telemetry_decision_category,
    telemetry_failure_isolated: diag.telemetry_failure_isolated,
    terminal_status: diag.terminal_status,
    transition_count: diag.transition_count,
    workflow_policy_version: diag.workflow_policy_version,
  };
}

const FORBIDDEN_DIAGNOSTIC_KEYS = [
  "workspace_path",
  "cli_path",
  "report_path",
  "stdout",
  "stderr",
  "command_arguments",
  "environment",
  "absolute_path",
] as const;

export function diagnosticsContainForbiddenKeys(
  blob: Record<string, unknown>
): string[] {
  const hits: string[] = [];
  for (const key of FORBIDDEN_DIAGNOSTIC_KEYS) {
    if (key in blob) {
      hits.push(key);
    }
  }
  const text = JSON.stringify(blob);
  if (text.includes("/Users/") || text.includes("/home/")) {
    hits.push("absolute_path_value");
  }
  return hits;
}
