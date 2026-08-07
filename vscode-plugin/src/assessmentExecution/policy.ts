/**
 * Community VS Code assessment-execution policy (Slice 13.5).
 * policy_id = community-vscode-assessment-execution-policy
 * policy_version = 1.0
 */

export const ASSESSMENT_EXECUTION_POLICY_ID =
  "community-vscode-assessment-execution-policy" as const;
export const ASSESSMENT_EXECUTION_POLICY_VERSION = "1.0" as const;

export type AssessmentExecutionPolicy = {
  readonly policy_id: typeof ASSESSMENT_EXECUTION_POLICY_ID;
  readonly policy_version: typeof ASSESSMENT_EXECUTION_POLICY_VERSION;
  readonly explicit_user_action_required: true;
  readonly workspace_required: true;
  readonly initialized_repository_required: true;
  readonly compatible_cli_required: true;
  readonly engine_cli_authoritative: true;
  readonly standard_product_invocation_count: 1;
  readonly ai_product_invocation_count: 1;
  readonly silent_retry_allowed: false;
  readonly silent_fallback_allowed: false;
  readonly command_local_consent_required: true;
  readonly telemetry_failure_isolated: true;
  readonly analytics_failure_isolated: true;
  readonly report_generation_engine_owned: true;
  readonly source_code_local: true;
  readonly repository_config_mutation_allowed: false;
  readonly git_mutation_allowed: false;
  /** Command ID selects AI vs standard — not settings alone. */
  readonly command_determines_ai_mode: true;
  readonly limitations: readonly string[];
};

export const DEFAULT_ASSESSMENT_EXECUTION_LIMITATIONS: readonly string[] = [
  "progress_complete_via_13_6",
  "report_opening_complete_via_13_7",
  "recovery_framework_available_via_13_8",
  "assessment_timeout_not_invented",
  "no_live_ai_provider_calls_in_tests",
  "no_full_extension_host_ui_automation",
  "worktree_uncommitted",
] as const;

export function createAssessmentExecutionPolicy(
  limitations: readonly string[] = DEFAULT_ASSESSMENT_EXECUTION_LIMITATIONS
): AssessmentExecutionPolicy {
  return {
    policy_id: ASSESSMENT_EXECUTION_POLICY_ID,
    policy_version: ASSESSMENT_EXECUTION_POLICY_VERSION,
    explicit_user_action_required: true,
    workspace_required: true,
    initialized_repository_required: true,
    compatible_cli_required: true,
    engine_cli_authoritative: true,
    standard_product_invocation_count: 1,
    ai_product_invocation_count: 1,
    silent_retry_allowed: false,
    silent_fallback_allowed: false,
    command_local_consent_required: true,
    telemetry_failure_isolated: true,
    analytics_failure_isolated: true,
    report_generation_engine_owned: true,
    source_code_local: true,
    repository_config_mutation_allowed: false,
    git_mutation_allowed: false,
    command_determines_ai_mode: true,
    limitations: [...limitations].sort(),
  };
}

export function assessmentExecutionPolicyToStableDict(
  policy: AssessmentExecutionPolicy
): Record<string, unknown> {
  return {
    ai_product_invocation_count: policy.ai_product_invocation_count,
    analytics_failure_isolated: policy.analytics_failure_isolated,
    command_determines_ai_mode: policy.command_determines_ai_mode,
    command_local_consent_required: policy.command_local_consent_required,
    compatible_cli_required: policy.compatible_cli_required,
    engine_cli_authoritative: policy.engine_cli_authoritative,
    explicit_user_action_required: policy.explicit_user_action_required,
    git_mutation_allowed: policy.git_mutation_allowed,
    initialized_repository_required: policy.initialized_repository_required,
    limitations: [...policy.limitations].sort(),
    policy_id: policy.policy_id,
    policy_version: policy.policy_version,
    report_generation_engine_owned: policy.report_generation_engine_owned,
    repository_config_mutation_allowed:
      policy.repository_config_mutation_allowed,
    silent_fallback_allowed: policy.silent_fallback_allowed,
    silent_retry_allowed: policy.silent_retry_allowed,
    source_code_local: policy.source_code_local,
    standard_product_invocation_count: policy.standard_product_invocation_count,
    telemetry_failure_isolated: policy.telemetry_failure_isolated,
    workspace_required: policy.workspace_required,
  };
}
