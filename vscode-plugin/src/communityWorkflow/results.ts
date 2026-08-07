/** Bounded Community workflow results (privacy-safe). */

import type { TelemetryDecisionCategory } from "./context";
import type { WorkflowOperation } from "./operations";
import type { WorkflowErrorCategory } from "./errors";

export const WORKFLOW_RESULT_STATUSES = [
  "success",
  "failure",
  "cancelled",
  "unavailable",
  "initialization_required",
] as const;

export type WorkflowResultStatus = (typeof WORKFLOW_RESULT_STATUSES)[number];

export type PrimaryExitCategory =
  | "success"
  | "failure"
  | "cancelled"
  | "unavailable"
  | "not_run";

export type CommunityWorkflowResult = {
  readonly operation: WorkflowOperation;
  readonly status: WorkflowResultStatus;
  readonly result_category: WorkflowErrorCategory | "ok";
  readonly report_available: boolean;
  readonly report_opened: boolean;
  readonly ai_requested: boolean;
  readonly telemetry_decision_category: TelemetryDecisionCategory;
  readonly primary_exit_category: PrimaryExitCategory;
  readonly recovery_category: "none" | "user_action_available";
  readonly limitations: readonly string[];
};

export function communityWorkflowResultToStableDict(
  result: CommunityWorkflowResult
): Record<string, unknown> {
  return {
    ai_requested: result.ai_requested,
    limitations: [...result.limitations].sort(),
    operation: result.operation,
    primary_exit_category: result.primary_exit_category,
    recovery_category: result.recovery_category,
    report_available: result.report_available,
    report_opened: result.report_opened,
    result_category: result.result_category,
    status: result.status,
    telemetry_decision_category: result.telemetry_decision_category,
  };
}
