/**
 * Command-scoped VS Code telemetry consent (Slice 9.13).
 * Never persisted to globalState, workspaceState, settings, or secretStorage.
 */

export type VsCodeTelemetryDecision =
  | "disabled_by_default"
  | "allowed_for_session"
  | "denied_for_session"
  | "non_interactive_disabled";

export type VsCodeTelemetryDecisionSource =
  | "default"
  | "interactive_prompt"
  | "explicit_command_option"
  | "non_interactive_policy";

export type VsCodeTelemetryConsent = {
  readonly decision: VsCodeTelemetryDecision;
  readonly source: VsCodeTelemetryDecisionSource;
  readonly explicit: boolean;
  readonly persisted: false;
  readonly priorConsentReused: false;
  readonly transmissionAuthorized: boolean;
  readonly scope: "command";
  readonly policyVersion: "1.0";
};

export function defaultConsent(): VsCodeTelemetryConsent {
  return {
    decision: "disabled_by_default",
    source: "default",
    explicit: false,
    persisted: false,
    priorConsentReused: false,
    transmissionAuthorized: false,
    scope: "command",
    policyVersion: "1.0",
  };
}

export function allowForSession(
  source: VsCodeTelemetryDecisionSource = "interactive_prompt"
): VsCodeTelemetryConsent {
  return {
    decision: "allowed_for_session",
    source,
    explicit: true,
    persisted: false,
    priorConsentReused: false,
    transmissionAuthorized: true,
    scope: "command",
    policyVersion: "1.0",
  };
}

export function denyForSession(
  source: VsCodeTelemetryDecisionSource = "interactive_prompt"
): VsCodeTelemetryConsent {
  return {
    decision: "denied_for_session",
    source,
    explicit: true,
    persisted: false,
    priorConsentReused: false,
    transmissionAuthorized: false,
    scope: "command",
    policyVersion: "1.0",
  };
}

export function nonInteractiveDisabledConsent(): VsCodeTelemetryConsent {
  return {
    decision: "non_interactive_disabled",
    source: "non_interactive_policy",
    explicit: true,
    persisted: false,
    priorConsentReused: false,
    transmissionAuthorized: false,
    scope: "command",
    policyVersion: "1.0",
  };
}

export function consentToStableDict(
  consent: VsCodeTelemetryConsent
): Record<string, unknown> {
  return {
    decision: consent.decision,
    explicit: consent.explicit,
    persisted: consent.persisted,
    policyVersion: consent.policyVersion,
    priorConsentReused: consent.priorConsentReused,
    scope: consent.scope,
    source: consent.source,
    transmissionAuthorized: consent.transmissionAuthorized,
  };
}
