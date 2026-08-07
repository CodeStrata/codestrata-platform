/**
 * Community VS Code clean-install / update validation policy (Slice 13.14).
 * policy_id = community-vscode-clean-install-policy
 * policy_version = 1.0
 *
 * Release-readiness validation for packaged VSIX install/update — not a feature slice.
 */

export const CLEAN_INSTALL_POLICY_ID =
  "community-vscode-clean-install-policy" as const;
export const CLEAN_INSTALL_POLICY_VERSION = "1.0" as const;

export const CLEAN_INSTALL_EXTENSION_VERSION = "0.2.0" as const;
export const CLEAN_INSTALL_SUPPORTED_CLI_FAMILY = "0.2.x" as const;

export type CleanInstallPolicy = {
  readonly policy_id: typeof CLEAN_INSTALL_POLICY_ID;
  readonly policy_version: typeof CLEAN_INSTALL_POLICY_VERSION;
  readonly extension_version: typeof CLEAN_INSTALL_EXTENSION_VERSION;
  readonly supported_cli_family: typeof CLEAN_INSTALL_SUPPORTED_CLI_FAMILY;
  readonly marketplace_publish_required: false;
  readonly vsix_install_required: true;
  readonly isolated_extension_home_required: true;
  readonly isolated_user_data_required: true;
  readonly developer_workspace_state_allowed: false;
  readonly developer_global_extension_state_allowed: false;
  readonly automatic_cli_install_allowed: false;
  readonly live_ai_provider_required: false;
  readonly production_telemetry_required: false;
  readonly machine_identity_allowed: false;
  readonly installation_identity_allowed: false;
  readonly update_validation_required: true;
  readonly uninstall_reinstall_validation_required: true;
  readonly limitations: readonly string[];
};

export const DEFAULT_CLEAN_INSTALL_LIMITATIONS: readonly string[] = [
  "full_extension_host_ui_automation_unavailable",
  "update_uses_synthetic_prior_package_when_no_historical_vsix",
  "uninstall_reinstall_automation_limited",
  "one_os_execution_with_cross_platform_static_coverage",
  "no_live_ai_provider_calls",
  "no_remote_marketplace_publish",
  "vsce_pinned_to_2_32_0_for_packaging_reliability",
  "epic_13_complete_via_13_15",
  "worktree_uncommitted",
] as const;

/** Stable setting keys expected to survive update. */
export const STABLE_SETTING_KEYS: readonly string[] = [
  "codestrata.engine.executable",
  "codestrata.assessment.outputDirectory",
  "codestrata.assessment.configPath",
  "codestrata.assessment.defaultNoAi",
  "codestrata.assessment.extraArgs",
  "codestrata.findings.groupBy",
  "codestrata.ai.providerHint",
] as const;

/** Stable command IDs expected after install/update. */
export const STABLE_COMMAND_IDS: readonly string[] = [
  "codestrata.assess",
  "codestrata.assessWithAi",
  "codestrata.init",
  "codestrata.openHtmlReport",
  "codestrata.installEngine",
  "codestrata.checkEnvironment",
  "codestrata.doctor",
] as const;

/** Allowed onboarding globalState keys (not telemetry consent). */
export const ALLOWED_ONBOARDING_STATE_KEYS: readonly string[] = [
  "codestrata.firstRunCompleted",
  "codestrata.welcomeDismissed",
] as const;

export const FORBIDDEN_PERSISTED_STATE_KEYS: readonly string[] = [
  "codestrata.telemetryConsent",
  "codestrata.telemetry.consent",
  "codestrata.analyticsConsent",
  "codestrata.installationId",
  "codestrata.machineId",
] as const;

export function createCleanInstallPolicy(
  limitations: readonly string[] = DEFAULT_CLEAN_INSTALL_LIMITATIONS
): CleanInstallPolicy {
  return {
    policy_id: CLEAN_INSTALL_POLICY_ID,
    policy_version: CLEAN_INSTALL_POLICY_VERSION,
    extension_version: CLEAN_INSTALL_EXTENSION_VERSION,
    supported_cli_family: CLEAN_INSTALL_SUPPORTED_CLI_FAMILY,
    marketplace_publish_required: false,
    vsix_install_required: true,
    isolated_extension_home_required: true,
    isolated_user_data_required: true,
    developer_workspace_state_allowed: false,
    developer_global_extension_state_allowed: false,
    automatic_cli_install_allowed: false,
    live_ai_provider_required: false,
    production_telemetry_required: false,
    machine_identity_allowed: false,
    installation_identity_allowed: false,
    update_validation_required: true,
    uninstall_reinstall_validation_required: true,
    limitations: [...limitations].sort(),
  };
}

export function cleanInstallPolicyToStableDict(
  policy: CleanInstallPolicy
): Record<string, unknown> {
  return {
    automatic_cli_install_allowed: policy.automatic_cli_install_allowed,
    developer_global_extension_state_allowed:
      policy.developer_global_extension_state_allowed,
    developer_workspace_state_allowed: policy.developer_workspace_state_allowed,
    extension_version: policy.extension_version,
    installation_identity_allowed: policy.installation_identity_allowed,
    isolated_extension_home_required: policy.isolated_extension_home_required,
    isolated_user_data_required: policy.isolated_user_data_required,
    limitations: [...policy.limitations].sort(),
    live_ai_provider_required: policy.live_ai_provider_required,
    machine_identity_allowed: policy.machine_identity_allowed,
    marketplace_publish_required: policy.marketplace_publish_required,
    policy_id: policy.policy_id,
    policy_version: policy.policy_version,
    production_telemetry_required: policy.production_telemetry_required,
    supported_cli_family: policy.supported_cli_family,
    uninstall_reinstall_validation_required:
      policy.uninstall_reinstall_validation_required,
    update_validation_required: policy.update_validation_required,
    vsix_install_required: policy.vsix_install_required,
  };
}
