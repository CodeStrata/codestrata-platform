/** Safe public workflow context (no paths / secrets). */

import type { WorkflowOperation } from "./operations";

export type WorkspaceKind =
  | "folder_workspace"
  | "multi_root_workspace"
  | "no_workspace"
  | "unsupported_workspace";

export type TelemetryDecisionCategory =
  | "allowed_for_session"
  | "denied"
  | "suppressed_non_interactive"
  | "not_applicable";

export type WorkflowContext = {
  readonly operation: WorkflowOperation;
  readonly workspace_available: boolean;
  readonly workspace_kind: WorkspaceKind;
  readonly repository_initialized: "initialized" | "not_initialized" | "unknown";
  readonly ai_requested: boolean;
  readonly telemetry_decision: TelemetryDecisionCategory;
  readonly output_mode: "notification_progress";
  readonly cancellation_supported: boolean;
};

export function createWorkflowContext(
  partial: WorkflowContext
): WorkflowContext {
  return {
    operation: partial.operation,
    workspace_available: partial.workspace_available,
    workspace_kind: partial.workspace_kind,
    repository_initialized: partial.repository_initialized,
    ai_requested: partial.ai_requested,
    telemetry_decision: partial.telemetry_decision,
    output_mode: partial.output_mode,
    cancellation_supported: partial.cancellation_supported,
  };
}

export function workflowContextToStableDict(
  ctx: WorkflowContext
): Record<string, unknown> {
  return {
    ai_requested: ctx.ai_requested,
    cancellation_supported: ctx.cancellation_supported,
    operation: ctx.operation,
    output_mode: ctx.output_mode,
    repository_initialized: ctx.repository_initialized,
    telemetry_decision: ctx.telemetry_decision,
    workspace_available: ctx.workspace_available,
    workspace_kind: ctx.workspace_kind,
  };
}
