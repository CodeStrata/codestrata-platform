/**
 * Epic 13 telemetry eligibility map (Slice 13.9).
 * Closed set — do not use string-prefix matching for eligibility.
 */

export const INTEGRATION_OPERATIONS = [
  "run_assessment",
  "run_assessment_with_ai",
  "initialize_repository",
  "open_report",
  "install_cli",
  "discover_cli",
  "doctor",
  "activation",
  "recovery_action",
] as const;

export type IntegrationOperation = (typeof INTEGRATION_OPERATIONS)[number];

export const ELIGIBLE_INTEGRATION_OPERATIONS = [
  "run_assessment",
  "run_assessment_with_ai",
] as const;

export type EligibleIntegrationOperation =
  (typeof ELIGIBLE_INTEGRATION_OPERATIONS)[number];

/** Explicit command ID → operation mapping (no prefix matching). */
export const COMMAND_TO_INTEGRATION_OPERATION: Readonly<
  Record<string, IntegrationOperation>
> = {
  "codestrata.assess": "run_assessment",
  "codestrata.assessWithAi": "run_assessment_with_ai",
  "codestrata.init": "initialize_repository",
  "codestrata.openHtmlReport": "open_report",
  "codestrata.installEngine": "install_cli",
  "codestrata.checkEnvironment": "doctor",
  "codestrata.doctor": "doctor",
  activation: "activation",
};

/** Recovery action labels that must not themselves open a consent prompt. */
export const RECOVERY_ACTIONS_TELEMETRY_INELIGIBLE = [
  "Initialize Repository",
  "Install CLI",
  "Correct CLI Setting",
  "Open Report",
  "Select Workspace",
  "Read Documentation",
  // "Run Assessment Again" starts a NEW codestrata.assess → fresh consent there.
] as const;

export function operationForCommandId(
  commandId: string
): IntegrationOperation | undefined {
  return COMMAND_TO_INTEGRATION_OPERATION[commandId];
}

export function isTelemetryEligibleOperation(
  operation: IntegrationOperation
): boolean {
  return (ELIGIBLE_INTEGRATION_OPERATIONS as readonly string[]).includes(
    operation
  );
}

export function isTelemetryEligibleCommand(commandId: string): boolean {
  const op = operationForCommandId(commandId);
  return op !== undefined && isTelemetryEligibleOperation(op);
}

export function eligibilityMapToStableDict(): Record<string, unknown> {
  const eligible = Object.entries(COMMAND_TO_INTEGRATION_OPERATION)
    .filter(([, op]) => isTelemetryEligibleOperation(op))
    .map(([command, operation]) => ({ command, operation }))
    .sort((a, b) => a.command.localeCompare(b.command));
  const ineligible = Object.entries(COMMAND_TO_INTEGRATION_OPERATION)
    .filter(([, op]) => !isTelemetryEligibleOperation(op))
    .map(([command, operation]) => ({ command, operation }))
    .sort((a, b) => a.command.localeCompare(b.command));
  return {
    eligible_commands: eligible,
    ineligible_commands: ineligible,
    recovery_actions_telemetry_ineligible: [
      ...RECOVERY_ACTIONS_TELEMETRY_INELIGIBLE,
    ].sort(),
  };
}
