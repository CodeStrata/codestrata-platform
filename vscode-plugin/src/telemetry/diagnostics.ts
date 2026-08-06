/**
 * Bounded VS Code telemetry diagnostics (Slice 9.13).
 * Never includes workspace, paths, repository, or installation identity.
 */

import type { VsCodeTelemetryConsent } from "./consent";
import {
  COMMUNITY_VSCODE_TELEMETRY_RUNTIME_POLICY_VERSION,
  VSCODE_TELEMETRY_EVENT_SCHEMA_VERSION,
} from "./runtimePolicy";

export type VsCodeTelemetryDiagnostics = {
  runtimePolicyVersion: string;
  eventSchemaVersion: string;
  decision: string;
  decisionSource: string;
  transmissionAuthorized: boolean;
  transportCategory: string;
  promptShown: boolean;
  eventsSeen: number;
  eventsProjected: number;
  eventsDropped: number;
  transportUnavailable: number;
  transportSent: number;
  failures: number;
};

export function createDiagnostics(options: {
  consent: VsCodeTelemetryConsent;
  transportCategory: string;
  promptShown?: boolean;
}): VsCodeTelemetryDiagnostics {
  return {
    runtimePolicyVersion: COMMUNITY_VSCODE_TELEMETRY_RUNTIME_POLICY_VERSION,
    eventSchemaVersion: VSCODE_TELEMETRY_EVENT_SCHEMA_VERSION,
    decision: options.consent.decision,
    decisionSource: options.consent.source,
    transmissionAuthorized: options.consent.transmissionAuthorized,
    transportCategory: options.transportCategory,
    promptShown: options.promptShown ?? false,
    eventsSeen: 0,
    eventsProjected: 0,
    eventsDropped: 0,
    transportUnavailable: 0,
    transportSent: 0,
    failures: 0,
  };
}

export function diagnosticsToStableDict(
  diagnostics: VsCodeTelemetryDiagnostics
): Record<string, unknown> {
  return {
    decision: diagnostics.decision,
    decisionSource: diagnostics.decisionSource,
    eventSchemaVersion: diagnostics.eventSchemaVersion,
    eventsDropped: diagnostics.eventsDropped,
    eventsProjected: diagnostics.eventsProjected,
    eventsSeen: diagnostics.eventsSeen,
    failures: diagnostics.failures,
    promptShown: diagnostics.promptShown,
    runtimePolicyVersion: diagnostics.runtimePolicyVersion,
    transmissionAuthorized: diagnostics.transmissionAuthorized,
    transportCategory: diagnostics.transportCategory,
    transportSent: diagnostics.transportSent,
    transportUnavailable: diagnostics.transportUnavailable,
  };
}
