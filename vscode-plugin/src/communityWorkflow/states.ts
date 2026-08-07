/** Closed workflow-state vocabulary (Slice 13.1). */

export const WORKFLOW_STATES = [
  "idle",
  "validating_workspace",
  "initializing",
  "awaiting_consent",
  "running_assessment",
  "locating_report",
  "opening_report",
  "completed",
  "failed",
  "cancelled",
] as const;

export type WorkflowState = (typeof WORKFLOW_STATES)[number];

export function isWorkflowState(value: string): value is WorkflowState {
  return (WORKFLOW_STATES as readonly string[]).includes(value);
}
