/**
 * Community VS Code CLI discovery policy (Slice 13.2).
 * policy_id = community-vscode-cli-discovery-policy
 * policy_version = 1.0
 */

export const CLI_DISCOVERY_POLICY_ID =
  "community-vscode-cli-discovery-policy" as const;
export const CLI_DISCOVERY_POLICY_VERSION = "1.0" as const;

export const DEFAULT_PROBE_TIMEOUT_SECONDS = 5 as const;
export const DEFAULT_MAX_PROBE_STDOUT_BYTES = 65_536 as const;
export const DEFAULT_MAX_PROBE_STDERR_BYTES = 65_536 as const;
export const DEFAULT_MAX_CANDIDATES = 8 as const;

export type CliDiscoveryPolicy = {
  readonly policy_id: typeof CLI_DISCOVERY_POLICY_ID;
  readonly policy_version: typeof CLI_DISCOVERY_POLICY_VERSION;
  readonly local_only: true;
  readonly network_allowed: false;
  readonly installation_allowed: false;
  readonly upgrade_allowed: false;
  readonly filesystem_crawl_allowed: false;
  readonly explicit_configuration_supported: true;
  readonly path_lookup_supported: true;
  readonly development_environment_supported: true;
  readonly identity_probe_required: true;
  readonly version_probe_required: true;
  readonly probe_timeout_seconds: number;
  readonly persistence_allowed: false;
  readonly environment_mutation_allowed: false;
  readonly invalid_explicit_fails_closed: true;
  readonly limitations: readonly string[];
};

export const DEFAULT_DISCOVERY_LIMITATIONS: readonly string[] = [
  "compatibility_matrix_delegated_to_13_11",
  "installation_guidance_only_see_13_3",
  "windows_wrapper_validated_via_mocks_only",
  "no_full_extension_host_ui_automation",
  "no_live_cli_installation_test",
  "process_local_cache_omitted",
] as const;

export function createCliDiscoveryPolicy(
  limitations: readonly string[] = DEFAULT_DISCOVERY_LIMITATIONS
): CliDiscoveryPolicy {
  return {
    policy_id: CLI_DISCOVERY_POLICY_ID,
    policy_version: CLI_DISCOVERY_POLICY_VERSION,
    local_only: true,
    network_allowed: false,
    installation_allowed: false,
    upgrade_allowed: false,
    filesystem_crawl_allowed: false,
    explicit_configuration_supported: true,
    path_lookup_supported: true,
    development_environment_supported: true,
    identity_probe_required: true,
    version_probe_required: true,
    probe_timeout_seconds: DEFAULT_PROBE_TIMEOUT_SECONDS,
    persistence_allowed: false,
    environment_mutation_allowed: false,
    invalid_explicit_fails_closed: true,
    limitations: [...limitations].sort(),
  };
}

export function cliDiscoveryPolicyToStableDict(
  policy: CliDiscoveryPolicy
): Record<string, unknown> {
  return {
    development_environment_supported: policy.development_environment_supported,
    explicit_configuration_supported: policy.explicit_configuration_supported,
    filesystem_crawl_allowed: policy.filesystem_crawl_allowed,
    identity_probe_required: policy.identity_probe_required,
    installation_allowed: policy.installation_allowed,
    invalid_explicit_fails_closed: policy.invalid_explicit_fails_closed,
    limitations: [...policy.limitations].sort(),
    local_only: policy.local_only,
    network_allowed: policy.network_allowed,
    path_lookup_supported: policy.path_lookup_supported,
    persistence_allowed: policy.persistence_allowed,
    environment_mutation_allowed: policy.environment_mutation_allowed,
    policy_id: policy.policy_id,
    policy_version: policy.policy_version,
    probe_timeout_seconds: policy.probe_timeout_seconds,
    upgrade_allowed: policy.upgrade_allowed,
    version_probe_required: policy.version_probe_required,
  };
}
