/**
 * Community VS Code failure-recovery policy (Slice 13.8).
 * policy_id = community-vscode-recovery-policy
 * policy_version = 1.0
 */

export const RECOVERY_POLICY_ID =
  "community-vscode-recovery-policy" as const;
export const RECOVERY_POLICY_VERSION = "1.0" as const;

export type FailureRecoveryPolicy = {
  readonly policy_id: typeof RECOVERY_POLICY_ID;
  readonly policy_version: typeof RECOVERY_POLICY_VERSION;
  readonly automatic_recovery_execution_allowed: false;
  readonly automatic_retry_allowed: false;
  readonly automatic_install_allowed: false;
  readonly automatic_assessment_rerun_allowed: false;
  readonly automatic_report_reopen_allowed: false;
  readonly user_triggered_actions_allowed: true;
  readonly primary_result_authoritative: true;
  readonly secondary_failure_isolated: true;
  readonly stack_traces_allowed: false;
  readonly paths_allowed: false;
  readonly cli_output_in_messages_allowed: false;
  readonly provider_details_allowed: false;
  readonly credentials_allowed: false;
  readonly telemetry_allowed: false;
  readonly analytics_allowed: false;
  readonly limitations: readonly string[];
};

export const DEFAULT_RECOVERY_LIMITATIONS: readonly string[] = [
  "user_triggered_actions_only",
  "no_automatic_retry",
  "no_full_extension_host_ui_automation",
  "marketplace_complete_via_13_12_13_13",
  "worktree_uncommitted",
] as const;

export function createFailureRecoveryPolicy(
  limitations: readonly string[] = DEFAULT_RECOVERY_LIMITATIONS
): FailureRecoveryPolicy {
  return {
    policy_id: RECOVERY_POLICY_ID,
    policy_version: RECOVERY_POLICY_VERSION,
    automatic_recovery_execution_allowed: false,
    automatic_retry_allowed: false,
    automatic_install_allowed: false,
    automatic_assessment_rerun_allowed: false,
    automatic_report_reopen_allowed: false,
    user_triggered_actions_allowed: true,
    primary_result_authoritative: true,
    secondary_failure_isolated: true,
    stack_traces_allowed: false,
    paths_allowed: false,
    cli_output_in_messages_allowed: false,
    provider_details_allowed: false,
    credentials_allowed: false,
    telemetry_allowed: false,
    analytics_allowed: false,
    limitations: [...limitations].sort(),
  };
}

export function failureRecoveryPolicyToStableDict(
  policy: FailureRecoveryPolicy
): Record<string, unknown> {
  return {
    analytics_allowed: policy.analytics_allowed,
    automatic_assessment_rerun_allowed:
      policy.automatic_assessment_rerun_allowed,
    automatic_install_allowed: policy.automatic_install_allowed,
    automatic_recovery_execution_allowed:
      policy.automatic_recovery_execution_allowed,
    automatic_report_reopen_allowed: policy.automatic_report_reopen_allowed,
    automatic_retry_allowed: policy.automatic_retry_allowed,
    cli_output_in_messages_allowed: policy.cli_output_in_messages_allowed,
    credentials_allowed: policy.credentials_allowed,
    limitations: [...policy.limitations].sort(),
    paths_allowed: policy.paths_allowed,
    policy_id: policy.policy_id,
    policy_version: policy.policy_version,
    primary_result_authoritative: policy.primary_result_authoritative,
    provider_details_allowed: policy.provider_details_allowed,
    secondary_failure_isolated: policy.secondary_failure_isolated,
    stack_traces_allowed: policy.stack_traces_allowed,
    telemetry_allowed: policy.telemetry_allowed,
    user_triggered_actions_allowed: policy.user_triggered_actions_allowed,
  };
}
