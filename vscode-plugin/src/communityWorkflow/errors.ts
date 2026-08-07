/** Bounded workflow error taxonomy (Slice 13.1). */

export const WORKFLOW_ERROR_CATEGORIES = [
  "workspace_unavailable",
  "workspace_unsupported",
  "repository_not_initialized",
  "initialization_failed",
  "cli_unavailable",
  "cli_incompatible",
  "cli_probe_failed",
  "invalid_cli_configuration",
  "cli_invocation_failed",
  "assessment_failed",
  "assessment_cancelled",
  "report_not_found",
  "report_open_failed",
  "telemetry_isolated_failure",
  "analytics_isolated_failure",
  "internal_workflow_error",
  "invalid_transition",
] as const;

export type WorkflowErrorCategory = (typeof WORKFLOW_ERROR_CATEGORIES)[number];

export class WorkflowTransitionError extends Error {
  readonly category: WorkflowErrorCategory = "invalid_transition";
  readonly fromState: string;
  readonly toState: string;

  constructor(fromState: string, toState: string) {
    super(`Invalid workflow transition: ${fromState} -> ${toState}`);
    this.name = "WorkflowTransitionError";
    this.fromState = fromState;
    this.toState = toState;
  }
}
