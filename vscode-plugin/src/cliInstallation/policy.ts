/**
 * Community VS Code CLI installation-guidance policy (Slice 13.3).
 * policy_id = community-vscode-cli-installation-policy
 * policy_version = 1.0
 *
 * Approach A — guidance-only. Automatic package-manager execution is forbidden.
 */

export const CLI_INSTALLATION_POLICY_ID =
  "community-vscode-cli-installation-policy" as const;
export const CLI_INSTALLATION_POLICY_VERSION = "1.0" as const;

export type InstallationApproach = "guidance_only";

export type CliInstallationPolicy = {
  readonly policy_id: typeof CLI_INSTALLATION_POLICY_ID;
  readonly policy_version: typeof CLI_INSTALLATION_POLICY_VERSION;
  readonly approach: InstallationApproach;
  readonly explicit_user_action_required: true;
  readonly activation_installation_allowed: false;
  readonly discovery_installation_allowed: false;
  readonly automatic_installation_allowed: false;
  readonly network_download_allowed: false;
  readonly arbitrary_script_execution_allowed: false;
  readonly privilege_escalation_allowed: false;
  readonly path_mutation_allowed: false;
  readonly shell_profile_mutation_allowed: false;
  readonly settings_mutation_allowed: false;
  readonly persistence_allowed: false;
  readonly supported_installation_methods: readonly string[];
  readonly discovery_refresh_available: true;
  readonly limitations: readonly string[];
};

export const DEFAULT_INSTALLATION_LIMITATIONS: readonly string[] = [
  "guidance_only_approach",
  "cli_install_guidance_complete_via_13_3",
  "compatibility_matrix_active_via_13_11",
  "platform_guidance_validated_via_mocks",
  "no_full_extension_host_ui_automation",
  "terminal_opened_without_auto_execute",
] as const;

export const SUPPORTED_INSTALLATION_METHOD_IDS = [
  "documentation",
  "python_package",
  "pipx",
  "uv_tool",
  "terminal_guidance",
] as const;

export function createCliInstallationPolicy(
  limitations: readonly string[] = DEFAULT_INSTALLATION_LIMITATIONS
): CliInstallationPolicy {
  return {
    policy_id: CLI_INSTALLATION_POLICY_ID,
    policy_version: CLI_INSTALLATION_POLICY_VERSION,
    approach: "guidance_only",
    explicit_user_action_required: true,
    activation_installation_allowed: false,
    discovery_installation_allowed: false,
    automatic_installation_allowed: false,
    network_download_allowed: false,
    arbitrary_script_execution_allowed: false,
    privilege_escalation_allowed: false,
    path_mutation_allowed: false,
    shell_profile_mutation_allowed: false,
    settings_mutation_allowed: false,
    persistence_allowed: false,
    supported_installation_methods: [...SUPPORTED_INSTALLATION_METHOD_IDS].sort(),
    discovery_refresh_available: true,
    limitations: [...limitations].sort(),
  };
}

export function cliInstallationPolicyToStableDict(
  policy: CliInstallationPolicy
): Record<string, unknown> {
  return {
    activation_installation_allowed: policy.activation_installation_allowed,
    approach: policy.approach,
    arbitrary_script_execution_allowed: policy.arbitrary_script_execution_allowed,
    automatic_installation_allowed: policy.automatic_installation_allowed,
    discovery_installation_allowed: policy.discovery_installation_allowed,
    discovery_refresh_available: policy.discovery_refresh_available,
    explicit_user_action_required: policy.explicit_user_action_required,
    limitations: [...policy.limitations].sort(),
    network_download_allowed: policy.network_download_allowed,
    path_mutation_allowed: policy.path_mutation_allowed,
    persistence_allowed: policy.persistence_allowed,
    policy_id: policy.policy_id,
    policy_version: policy.policy_version,
    privilege_escalation_allowed: policy.privilege_escalation_allowed,
    settings_mutation_allowed: policy.settings_mutation_allowed,
    shell_profile_mutation_allowed: policy.shell_profile_mutation_allowed,
    supported_installation_methods: [...policy.supported_installation_methods].sort(),
  };
}
