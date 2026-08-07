/** Explicit workflow state transitions (Slice 13.1). */

import { WorkflowTransitionError } from "./errors";
import type { WorkflowState } from "./states";

/**
 * Allowed edges. Terminal states (completed/failed/cancelled) only accept
 * return to idle for a subsequent operation.
 */
export const ALLOWED_TRANSITIONS: Readonly<
  Record<WorkflowState, readonly WorkflowState[]>
> = {
  idle: ["validating_workspace", "opening_report"],
  validating_workspace: [
    "initializing",
    "awaiting_consent",
    "opening_report",
    // Slice 13.4: already-initialized / invalid-config may complete without
    // entering `initializing` (no Engine product invocation).
    "completed",
    "failed",
    "cancelled",
  ],
  initializing: ["completed", "failed", "cancelled"],
  awaiting_consent: ["running_assessment", "failed", "cancelled"],
  running_assessment: [
    "locating_report",
    "completed",
    "failed",
    "cancelled",
  ],
  locating_report: ["opening_report", "completed", "failed"],
  opening_report: ["completed", "failed"],
  completed: ["idle"],
  failed: ["idle"],
  cancelled: ["idle"],
};

export function canTransition(from: WorkflowState, to: WorkflowState): boolean {
  return ALLOWED_TRANSITIONS[from].includes(to);
}

export function assertTransition(from: WorkflowState, to: WorkflowState): void {
  if (!canTransition(from, to)) {
    throw new WorkflowTransitionError(from, to);
  }
}
