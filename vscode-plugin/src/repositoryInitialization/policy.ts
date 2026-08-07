/**
 * Community VS Code repository initialization policy (Slice 13.4).
 * policy_id = community-vscode-repository-initialization-policy
 * policy_version = 1.0
 */

export const REPO_INIT_POLICY_ID =
  "community-vscode-repository-initialization-policy" as const;
export const REPO_INIT_POLICY_VERSION = "1.0" as const;

/** Fixed Engine-owned configuration basename (not a repository-specific path). */
export const CODESTRATA_CONFIG_BASENAME = "codestrata.toml" as const;

export type RepositoryInitializationPolicy = {
  readonly policy_id: typeof REPO_INIT_POLICY_ID;
  readonly policy_version: typeof REPO_INIT_POLICY_VERSION;
  readonly explicit_user_action_required: true;
  readonly workspace_required: true;
  readonly compatible_cli_required: true;
  readonly engine_cli_authoritative: true;
  readonly product_cli_invocation_count: 1;
  readonly assessment_allowed: false;
  readonly ai_execution_allowed: false;
  readonly telemetry_consent_allowed: false;
  readonly analytics_allowed: false;
  readonly report_open_allowed: false;
  readonly source_file_mutation_allowed: false;
  readonly config_mutation_owned_by_engine: true;
  readonly repeat_initialization_safe: true;
  readonly automatic_overwrite_allowed: false;
  readonly local_only: true;
  readonly already_initialized_skips_cli: true;
  readonly limitations: readonly string[];
};

export const DEFAULT_REPO_INIT_LIMITATIONS: readonly string[] = [
  "engine_init_output_retained",
  "multi_root_selection_ux_retained",
  "cancellation_ui_not_redesigned",
  "recovery_framework_available_via_13_8",
  "no_full_extension_host_ui_automation",
] as const;

export function createRepositoryInitializationPolicy(
  limitations: readonly string[] = DEFAULT_REPO_INIT_LIMITATIONS
): RepositoryInitializationPolicy {
  return {
    policy_id: REPO_INIT_POLICY_ID,
    policy_version: REPO_INIT_POLICY_VERSION,
    explicit_user_action_required: true,
    workspace_required: true,
    compatible_cli_required: true,
    engine_cli_authoritative: true,
    product_cli_invocation_count: 1,
    assessment_allowed: false,
    ai_execution_allowed: false,
    telemetry_consent_allowed: false,
    analytics_allowed: false,
    report_open_allowed: false,
    source_file_mutation_allowed: false,
    config_mutation_owned_by_engine: true,
    repeat_initialization_safe: true,
    automatic_overwrite_allowed: false,
    local_only: true,
    already_initialized_skips_cli: true,
    limitations: [...limitations].sort(),
  };
}

export function repositoryInitializationPolicyToStableDict(
  policy: RepositoryInitializationPolicy
): Record<string, unknown> {
  return {
    already_initialized_skips_cli: policy.already_initialized_skips_cli,
    ai_execution_allowed: policy.ai_execution_allowed,
    analytics_allowed: policy.analytics_allowed,
    assessment_allowed: policy.assessment_allowed,
    automatic_overwrite_allowed: policy.automatic_overwrite_allowed,
    compatible_cli_required: policy.compatible_cli_required,
    config_mutation_owned_by_engine: policy.config_mutation_owned_by_engine,
    engine_cli_authoritative: policy.engine_cli_authoritative,
    explicit_user_action_required: policy.explicit_user_action_required,
    limitations: [...policy.limitations].sort(),
    local_only: policy.local_only,
    policy_id: policy.policy_id,
    policy_version: policy.policy_version,
    product_cli_invocation_count: policy.product_cli_invocation_count,
    repeat_initialization_safe: policy.repeat_initialization_safe,
    report_open_allowed: policy.report_open_allowed,
    source_file_mutation_allowed: policy.source_file_mutation_allowed,
    telemetry_consent_allowed: policy.telemetry_consent_allowed,
    workspace_required: policy.workspace_required,
  };
}
