/** Integration diagnostics (privacy-safe, Slice 13.9). */

import { TELEMETRY_INTEGRATION_POLICY_VERSION } from "./policy";
import type { ConsentOrderingResult } from "./ordering";

export type TelemetryIntegrationDiagnostics = {
  readonly integration_policy_version: typeof TELEMETRY_INTEGRATION_POLICY_VERSION;
  readonly operation: string;
  readonly eligible: boolean;
  readonly readiness_passed: boolean;
  readonly consent_prompt_attempted: boolean;
  readonly consent_prompt_count: number;
  readonly consent_decision_category: string;
  readonly consent_reused: false;
  readonly persisted: false;
  readonly identity_used: false;
  readonly telemetry_runtime_created: boolean;
  readonly telemetry_transport_category: "unavailable" | "capture" | "none";
  readonly analytics_constructed: boolean;
  readonly analytics_sink_category: "unavailable" | "capture" | "none";
  readonly primary_result_preserved: true;
  readonly limitations: readonly string[];
};

const FORBIDDEN_KEYS = [
  "path",
  "uri",
  "workspace",
  "stdout",
  "stderr",
  "stack",
  "exception",
  "credential",
  "password",
  "token",
  "api_key",
  "machineId",
  "installation_id",
  "provider",
  "model",
  "timestamp",
] as const;

export function createIntegrationDiagnostics(options: {
  readonly operation: string;
  readonly eligible: boolean;
  readonly ordering: ConsentOrderingResult;
  readonly consentPromptAttempted: boolean;
  readonly consentPromptCount: number;
  readonly consentDecisionCategory: string;
  readonly telemetryRuntimeCreated: boolean;
  readonly telemetryTransportCategory: "unavailable" | "capture" | "none";
  readonly analyticsConstructed: boolean;
  readonly analyticsSinkCategory: "unavailable" | "capture" | "none";
  readonly limitations: readonly string[];
}): TelemetryIntegrationDiagnostics {
  return {
    integration_policy_version: TELEMETRY_INTEGRATION_POLICY_VERSION,
    operation: options.operation,
    eligible: options.eligible,
    readiness_passed: options.ordering.readiness_passed,
    consent_prompt_attempted: options.consentPromptAttempted,
    consent_prompt_count: options.consentPromptCount,
    consent_decision_category: options.consentDecisionCategory,
    consent_reused: false,
    persisted: false,
    identity_used: false,
    telemetry_runtime_created: options.telemetryRuntimeCreated,
    telemetry_transport_category: options.telemetryTransportCategory,
    analytics_constructed: options.analyticsConstructed,
    analytics_sink_category: options.analyticsSinkCategory,
    primary_result_preserved: true,
    limitations: [...options.limitations].sort(),
  };
}

export function integrationDiagnosticsToStableDict(
  diagnostics: TelemetryIntegrationDiagnostics
): Record<string, unknown> {
  return {
    analytics_constructed: diagnostics.analytics_constructed,
    analytics_sink_category: diagnostics.analytics_sink_category,
    consent_decision_category: diagnostics.consent_decision_category,
    consent_prompt_attempted: diagnostics.consent_prompt_attempted,
    consent_prompt_count: diagnostics.consent_prompt_count,
    consent_reused: diagnostics.consent_reused,
    eligible: diagnostics.eligible,
    identity_used: diagnostics.identity_used,
    integration_policy_version: diagnostics.integration_policy_version,
    limitations: [...diagnostics.limitations].sort(),
    operation: diagnostics.operation,
    persisted: diagnostics.persisted,
    primary_result_preserved: diagnostics.primary_result_preserved,
    readiness_passed: diagnostics.readiness_passed,
    telemetry_runtime_created: diagnostics.telemetry_runtime_created,
    telemetry_transport_category: diagnostics.telemetry_transport_category,
  };
}

export function integrationDiagnosticsContainForbiddenKeys(
  value: Record<string, unknown>
): boolean {
  const blob = JSON.stringify(value).toLowerCase();
  if (blob.includes("/users/") || blob.includes("file://")) {
    return true;
  }
  for (const key of FORBIDDEN_KEYS) {
    if (Object.prototype.hasOwnProperty.call(value, key)) {
      return true;
    }
  }
  return false;
}
