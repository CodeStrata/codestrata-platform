/**
 * Community VS Code workflow policy (Slice 13.1).
 * policy_id = community-vscode-workflow-policy
 * policy_version = 1.0
 */

export const WORKFLOW_POLICY_ID = "community-vscode-workflow-policy" as const;
export const WORKFLOW_POLICY_VERSION = "1.0" as const;

export type CommunityWorkflowPolicy = {
  readonly policy_id: typeof WORKFLOW_POLICY_ID;
  readonly policy_version: typeof WORKFLOW_POLICY_VERSION;
  readonly activation_is_lightweight: true;
  readonly commands_are_user_triggered: true;
  readonly initialization_is_explicit: true;
  readonly assessment_uses_cli: true;
  readonly cli_invocation_count: 1;
  readonly source_code_remains_local: true;
  readonly telemetry_consent_scope: "command";
  readonly telemetry_transport: "unavailable";
  readonly analytics_sink: "unavailable";
  readonly primary_operation_authoritative: true;
  readonly report_opening_is_local: true;
  readonly installation_automation_available: false;
  readonly compatibility_detection_available: false;
  readonly limitations: readonly string[];
};

export const DEFAULT_WORKFLOW_LIMITATIONS: readonly string[] = [
  "progress_ui_retained_until_13_6",
  "report_opening_ux_retained_until_13_7",
  "recovery_framework_active_13_8",
  "version_compatibility_active_13_11",
  "marketplace_complete_via_13_12_13_13",
  "no_full_extension_host_ui_automation",
] as const;

export function createWorkflowPolicy(
  limitations: readonly string[] = DEFAULT_WORKFLOW_LIMITATIONS
): CommunityWorkflowPolicy {
  return {
    policy_id: WORKFLOW_POLICY_ID,
    policy_version: WORKFLOW_POLICY_VERSION,
    activation_is_lightweight: true,
    commands_are_user_triggered: true,
    initialization_is_explicit: true,
    assessment_uses_cli: true,
    cli_invocation_count: 1,
    source_code_remains_local: true,
    telemetry_consent_scope: "command",
    telemetry_transport: "unavailable",
    analytics_sink: "unavailable",
    primary_operation_authoritative: true,
    report_opening_is_local: true,
    installation_automation_available: false,
    compatibility_detection_available: false,
    limitations: [...limitations].sort(),
  };
}

export function workflowPolicyToStableDict(
  policy: CommunityWorkflowPolicy
): Record<string, unknown> {
  return {
    activation_is_lightweight: policy.activation_is_lightweight,
    analytics_sink: policy.analytics_sink,
    assessment_uses_cli: policy.assessment_uses_cli,
    cli_invocation_count: policy.cli_invocation_count,
    commands_are_user_triggered: policy.commands_are_user_triggered,
    compatibility_detection_available: policy.compatibility_detection_available,
    initialization_is_explicit: policy.initialization_is_explicit,
    installation_automation_available: policy.installation_automation_available,
    limitations: [...policy.limitations].sort(),
    policy_id: policy.policy_id,
    policy_version: policy.policy_version,
    primary_operation_authoritative: policy.primary_operation_authoritative,
    report_opening_is_local: policy.report_opening_is_local,
    source_code_remains_local: policy.source_code_remains_local,
    telemetry_consent_scope: policy.telemetry_consent_scope,
    telemetry_transport: policy.telemetry_transport,
  };
}
