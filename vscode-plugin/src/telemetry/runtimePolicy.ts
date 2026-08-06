/**
 * Community VS Code telemetry runtime policy (Slice 9.13).
 * Independently versioned from Engine runtime policy.
 */

export const COMMUNITY_VSCODE_TELEMETRY_RUNTIME_POLICY_ID =
  "community-vscode-telemetry-runtime-policy";
export const COMMUNITY_VSCODE_TELEMETRY_RUNTIME_POLICY_VERSION = "1.0";
export const COMMUNITY_VSCODE_TELEMETRY_RUNTIME_POLICY_URN = `${COMMUNITY_VSCODE_TELEMETRY_RUNTIME_POLICY_ID}:${COMMUNITY_VSCODE_TELEMETRY_RUNTIME_POLICY_VERSION}`;

export const VSCODE_TELEMETRY_EVENT_SCHEMA_NAME =
  "community-vscode-telemetry-event-schema";
export const VSCODE_TELEMETRY_EVENT_SCHEMA_VERSION = "1.0";

const LIMITATIONS = [
  "disabled_by_default",
  "command_scoped_consent",
  "no_persisted_consent",
  "no_prior_consent_reuse",
  "no_installation_identity",
  "no_workspace_repository_document_collection",
  "no_path_collection",
  "no_finding_evidence_collection",
  "no_prompt_response_collection",
  "no_credentials",
  "no_exact_provider_model_token_cost",
  "bounded_event_types",
  "preview_available",
  "unavailable_transport",
  "fail_silent_isolation",
  "no_queue",
  "no_retry",
  "http_transport_deferred",
  "platform_extension_event_mapping_deferred",
  "cursor_integration_deferred",
] as const;

export type VsCodeTelemetryRuntimePolicy = {
  readonly policyId: string;
  readonly policyVersion: string;
  readonly policyToken: string;
  readonly eventSchemaName: string;
  readonly eventSchemaVersion: string;
  readonly disabledByDefault: true;
  readonly commandScopedConsent: true;
  readonly noPersistedConsent: true;
  readonly noPriorConsentReuse: true;
  readonly noInstallationIdentity: true;
  readonly unavailableTransport: true;
  readonly failSilentIsolation: true;
  readonly noQueue: true;
  readonly noRetry: true;
  readonly limitations: readonly string[];
};

export function defaultVsCodeTelemetryRuntimePolicy(): VsCodeTelemetryRuntimePolicy {
  return {
    policyId: COMMUNITY_VSCODE_TELEMETRY_RUNTIME_POLICY_ID,
    policyVersion: COMMUNITY_VSCODE_TELEMETRY_RUNTIME_POLICY_VERSION,
    policyToken: COMMUNITY_VSCODE_TELEMETRY_RUNTIME_POLICY_URN,
    eventSchemaName: VSCODE_TELEMETRY_EVENT_SCHEMA_NAME,
    eventSchemaVersion: VSCODE_TELEMETRY_EVENT_SCHEMA_VERSION,
    disabledByDefault: true,
    commandScopedConsent: true,
    noPersistedConsent: true,
    noPriorConsentReuse: true,
    noInstallationIdentity: true,
    unavailableTransport: true,
    failSilentIsolation: true,
    noQueue: true,
    noRetry: true,
    limitations: [...LIMITATIONS].sort(),
  };
}

export function policyToStableDict(
  policy: VsCodeTelemetryRuntimePolicy = defaultVsCodeTelemetryRuntimePolicy()
): Record<string, unknown> {
  return {
    commandScopedConsent: policy.commandScopedConsent,
    disabledByDefault: policy.disabledByDefault,
    eventSchemaName: policy.eventSchemaName,
    eventSchemaVersion: policy.eventSchemaVersion,
    failSilentIsolation: policy.failSilentIsolation,
    limitations: [...policy.limitations],
    noInstallationIdentity: policy.noInstallationIdentity,
    noPersistedConsent: policy.noPersistedConsent,
    noPriorConsentReuse: policy.noPriorConsentReuse,
    noQueue: policy.noQueue,
    noRetry: policy.noRetry,
    policyId: policy.policyId,
    policyToken: policy.policyToken,
    policyVersion: policy.policyVersion,
    unavailableTransport: policy.unavailableTransport,
  };
}
