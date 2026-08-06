/**
 * Interactive prompt eligibility for VS Code telemetry (Slice 9.13).
 */

export const ELIGIBLE_TELEMETRY_COMMANDS = [
  "codestrata.assess",
  "codestrata.assessWithAi",
] as const;

export type EligibleTelemetryCommand =
  (typeof ELIGIBLE_TELEMETRY_COMMANDS)[number];

export const EXCLUDED_TELEMETRY_COMMANDS = [
  "codestrata.installEngine",
  "codestrata.checkEnvironment",
  "codestrata.doctor",
  "codestrata.init",
  "codestrata.openHtmlReport",
  "codestrata.refreshFindings",
  "codestrata.refreshRecommendations",
  "codestrata.showRecommendations",
  "codestrata.clearResults",
  "codestrata.openOutput",
  "codestrata.openDocumentation",
  "codestrata.showWelcome",
  "codestrata.setFindingsGroupBy",
  "codestrata.filterFindings",
  "codestrata.openFindingLocation",
  "activation",
] as const;

export type PromptEligibilityReason =
  | "eligible"
  | "command_not_eligible"
  | "non_interactive"
  | "decision_already_explicit";

export type PromptEligibility = {
  readonly eligible: boolean;
  readonly reason: PromptEligibilityReason;
};

export function isEligibleTelemetryCommand(commandId: string): boolean {
  return (ELIGIBLE_TELEMETRY_COMMANDS as readonly string[]).includes(commandId);
}

export function evaluatePromptEligibility(options: {
  commandId: string;
  interactive: boolean;
  decisionAlreadyExplicit?: boolean;
}): PromptEligibility {
  if (options.decisionAlreadyExplicit) {
    return { eligible: false, reason: "decision_already_explicit" };
  }
  if (!options.interactive) {
    return { eligible: false, reason: "non_interactive" };
  }
  if (!isEligibleTelemetryCommand(options.commandId)) {
    return { eligible: false, reason: "command_not_eligible" };
  }
  return { eligible: true, reason: "eligible" };
}
