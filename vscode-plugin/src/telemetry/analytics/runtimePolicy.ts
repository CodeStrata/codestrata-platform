/**
 * Community VS Code anonymous analytics policy (Epic 10 Slice 10.7).
 * Independently versioned from Engine analytics and VS Code telemetry runtime.
 */

export const COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_POLICY_ID =
  "community-vscode-anonymous-analytics-policy";
export const COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_POLICY_VERSION = "1.0";
export const COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_POLICY_URN = `${COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_POLICY_ID}:${COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_POLICY_VERSION}`;

export const COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_SCHEMA_ID =
  "community-vscode-anonymous-analytics-schema";
export const COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_SCHEMA_VERSION = "1.0";
export const COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_SCHEMA_URN = `${COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_SCHEMA_ID}:${COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_SCHEMA_VERSION}`;

const LIMITATIONS = [
  "local_construction_only",
  "persistence_disabled",
  "transmission_disabled",
  "disabled_by_default_runtime_prerequisite",
  "command_local_consent_prerequisite",
  "mandatory_privacy_projection",
  "identity_free_in_slice_10_7",
  "no_machine_workspace_repository_document_identity",
  "no_installation_identity",
  "no_engine_identity_file_coupling",
  "no_http",
  "no_queue",
  "no_retry",
  "unavailable_sink_default",
  "primary_command_isolation_required",
  "no_output_or_argv_collection",
  "provider_model_analytics_deferred_to_engine",
  "platform_extension_event_mapping_deferred",
  "cursor_excluded",
  "slice_10_8_owns_full_privacy_verification",
  "release_adoption_without_marketplace_authority",
] as const;

export type VsCodeAnonymousAnalyticsPolicy = {
  readonly policyId: string;
  readonly policyVersion: string;
  readonly policyToken: string;
  readonly schemaId: string;
  readonly schemaVersion: string;
  readonly schemaToken: string;
  readonly telemetryRuntimePolicyVersion: "1.0";
  readonly telemetryEventSchemaVersion: "1.0";
  readonly localConstructionOnly: true;
  readonly persistenceEnabled: false;
  readonly transmissionEnabled: false;
  readonly installationIdentityAllowed: false;
  readonly unavailableSinkDefault: true;
  readonly requiresCommandLocalConsent: true;
  readonly requiresPrivacyProjection: true;
  readonly failSilentIsolation: true;
  readonly noHttp: true;
  readonly noQueue: true;
  readonly noRetry: true;
  readonly limitations: readonly string[];
};

export function defaultVsCodeAnonymousAnalyticsPolicy(): VsCodeAnonymousAnalyticsPolicy {
  return {
    policyId: COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_POLICY_ID,
    policyVersion: COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_POLICY_VERSION,
    policyToken: COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_POLICY_URN,
    schemaId: COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_SCHEMA_ID,
    schemaVersion: COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_SCHEMA_VERSION,
    schemaToken: COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_SCHEMA_URN,
    telemetryRuntimePolicyVersion: "1.0",
    telemetryEventSchemaVersion: "1.0",
    localConstructionOnly: true,
    persistenceEnabled: false,
    transmissionEnabled: false,
    installationIdentityAllowed: false,
    unavailableSinkDefault: true,
    requiresCommandLocalConsent: true,
    requiresPrivacyProjection: true,
    failSilentIsolation: true,
    noHttp: true,
    noQueue: true,
    noRetry: true,
    limitations: [...LIMITATIONS].sort(),
  };
}

export function analyticsPolicyToStableDict(
  policy: VsCodeAnonymousAnalyticsPolicy = defaultVsCodeAnonymousAnalyticsPolicy()
): Record<string, unknown> {
  return {
    failSilentIsolation: policy.failSilentIsolation,
    installationIdentityAllowed: policy.installationIdentityAllowed,
    limitations: [...policy.limitations],
    localConstructionOnly: policy.localConstructionOnly,
    noHttp: policy.noHttp,
    noQueue: policy.noQueue,
    noRetry: policy.noRetry,
    persistenceEnabled: policy.persistenceEnabled,
    policyId: policy.policyId,
    policyToken: policy.policyToken,
    policyVersion: policy.policyVersion,
    requiresCommandLocalConsent: policy.requiresCommandLocalConsent,
    requiresPrivacyProjection: policy.requiresPrivacyProjection,
    schemaId: policy.schemaId,
    schemaToken: policy.schemaToken,
    schemaVersion: policy.schemaVersion,
    telemetryEventSchemaVersion: policy.telemetryEventSchemaVersion,
    telemetryRuntimePolicyVersion: policy.telemetryRuntimePolicyVersion,
    transmissionEnabled: policy.transmissionEnabled,
    unavailableSinkDefault: policy.unavailableSinkDefault,
  };
}
