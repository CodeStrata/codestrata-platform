/** Closed workflow operations and command ID mapping (Slice 13.1). */

export const WORKFLOW_OPERATIONS = [
  "initialize_repository",
  "run_assessment",
  "run_assessment_with_ai",
  "open_report",
] as const;

export type WorkflowOperation = (typeof WORKFLOW_OPERATIONS)[number];

/** Commands that participate in the Community workflow contract. */
export const WORKFLOW_COMMAND_IDS = [
  "codestrata.init",
  "codestrata.assess",
  "codestrata.assessWithAi",
  "codestrata.openHtmlReport",
] as const;

export type WorkflowCommandId = (typeof WORKFLOW_COMMAND_IDS)[number];

export const COMMAND_TO_OPERATION: Record<WorkflowCommandId, WorkflowOperation> = {
  "codestrata.init": "initialize_repository",
  "codestrata.assess": "run_assessment",
  "codestrata.assessWithAi": "run_assessment_with_ai",
  "codestrata.openHtmlReport": "open_report",
};

/** Compatibility alias: doctor re-executes checkEnvironment (not a workflow operation). */
export const COMPATIBILITY_ALIASES: ReadonlyArray<{
  readonly alias: string;
  readonly target: string;
}> = [{ alias: "codestrata.doctor", target: "codestrata.checkEnvironment" }];

export function operationForCommand(
  commandId: string
): WorkflowOperation | undefined {
  if ((WORKFLOW_COMMAND_IDS as readonly string[]).includes(commandId)) {
    return COMMAND_TO_OPERATION[commandId as WorkflowCommandId];
  }
  return undefined;
}

export function isWorkflowOperation(value: string): value is WorkflowOperation {
  return (WORKFLOW_OPERATIONS as readonly string[]).includes(value);
}
