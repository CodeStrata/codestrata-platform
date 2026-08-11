/**
 * Community VS Code telemetry consent integration policy (Slice 19.4).
 * policy_id = community-vscode-telemetry-integration-policy
 * policy_version = 2.0
 *
 * Describes how Community workflow uses the telemetry runtime with local
 * preference persistence. Does not replace community-vscode-telemetry-runtime-policy:2.0.
 */

export const TELEMETRY_INTEGRATION_POLICY_ID =
  "community-vscode-telemetry-integration-policy" as const;
export const TELEMETRY_INTEGRATION_POLICY_VERSION = "2.0" as const;

/** Runtime policy this integration attaches to. */
export const TELEMETRY_RUNTIME_POLICY_REF =
  "community-vscode-telemetry-runtime-policy:2.0" as const;

export type TelemetryIntegrationPolicy = {
  readonly policy_id: typeof TELEMETRY_INTEGRATION_POLICY_ID;
  readonly policy_version: typeof TELEMETRY_INTEGRATION_POLICY_VERSION;
  readonly telemetry_runtime_policy_version: "2.0";
  readonly eligible_operations: readonly [
    "run_assessment",
    "run_assessment_with_ai",
  ];
  readonly consent_scope: "command";
  readonly default_decision: "deny";
  readonly persistence_allowed: true;
  readonly prior_consent_reuse_allowed: true;
  readonly installation_identity_allowed: false;
  readonly machine_identity_allowed: false;
  readonly non_interactive_prompt_allowed: false;
  readonly unavailable_transport_required: true;
  readonly analytics_requires_allowed_consent: true;
  readonly activation_eligible: false;
  readonly initialization_eligible: false;
  readonly discovery_eligible: false;
  readonly installation_guidance_eligible: false;
  readonly report_open_eligible: false;
  readonly recovery_eligible: false;
  readonly primary_operation_authoritative: true;
  readonly limitations: readonly string[];
};

export const DEFAULT_TELEMETRY_INTEGRATION_LIMITATIONS: readonly string[] = [
  "transport_remains_unavailable",
  "local_preference_persistence",
  "no_default_yes",
  "no_installation_identity",
  "source_locality_verified_in_13_10",
  "marketplace_complete_via_13_12_13_13",
] as const;

export function createTelemetryIntegrationPolicy(
  limitations: readonly string[] = DEFAULT_TELEMETRY_INTEGRATION_LIMITATIONS
): TelemetryIntegrationPolicy {
  return {
    policy_id: TELEMETRY_INTEGRATION_POLICY_ID,
    policy_version: TELEMETRY_INTEGRATION_POLICY_VERSION,
    telemetry_runtime_policy_version: "2.0",
    eligible_operations: ["run_assessment", "run_assessment_with_ai"],
    consent_scope: "command",
    default_decision: "deny",
    persistence_allowed: true,
    prior_consent_reuse_allowed: true,
    installation_identity_allowed: false,
    machine_identity_allowed: false,
    non_interactive_prompt_allowed: false,
    unavailable_transport_required: true,
    analytics_requires_allowed_consent: true,
    activation_eligible: false,
    initialization_eligible: false,
    discovery_eligible: false,
    installation_guidance_eligible: false,
    report_open_eligible: false,
    recovery_eligible: false,
    primary_operation_authoritative: true,
    limitations: [...limitations].sort(),
  };
}

export function telemetryIntegrationPolicyToStableDict(
  policy: TelemetryIntegrationPolicy
): Record<string, unknown> {
  return {
    activation_eligible: policy.activation_eligible,
    analytics_requires_allowed_consent:
      policy.analytics_requires_allowed_consent,
    consent_scope: policy.consent_scope,
    default_decision: policy.default_decision,
    discovery_eligible: policy.discovery_eligible,
    eligible_operations: [...policy.eligible_operations].sort(),
    initialization_eligible: policy.initialization_eligible,
    installation_guidance_eligible: policy.installation_guidance_eligible,
    installation_identity_allowed: policy.installation_identity_allowed,
    limitations: [...policy.limitations].sort(),
    machine_identity_allowed: policy.machine_identity_allowed,
    non_interactive_prompt_allowed: policy.non_interactive_prompt_allowed,
    persistence_allowed: policy.persistence_allowed,
    policy_id: policy.policy_id,
    policy_version: policy.policy_version,
    prior_consent_reuse_allowed: policy.prior_consent_reuse_allowed,
    primary_operation_authoritative: policy.primary_operation_authoritative,
    recovery_eligible: policy.recovery_eligible,
    report_open_eligible: policy.report_open_eligible,
    telemetry_runtime_policy_version: policy.telemetry_runtime_policy_version,
    unavailable_transport_required: policy.unavailable_transport_required,
  };
}
