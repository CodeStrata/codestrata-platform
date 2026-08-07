/**
 * Community VS Code CLI–extension compatibility policy (Slice 13.11).
 * policy_id = community-vscode-cli-compatibility-policy
 * policy_version = 1.0
 *
 * Independent from discovery: discovery finds a CLI; compatibility decides support.
 */

export const CLI_COMPATIBILITY_POLICY_ID =
  "community-vscode-cli-compatibility-policy" as const;
export const CLI_COMPATIBILITY_POLICY_VERSION = "1.0" as const;

export const COMPATIBILITY_EXTENSION_VERSION = "0.2.0" as const;
export const COMPATIBILITY_SUPPORTED_MAJOR = 0 as const;
export const COMPATIBILITY_MINIMUM_CLI = "0.2.0" as const;
export const COMPATIBILITY_MAXIMUM_CLI_MAJOR = 0 as const;

export type CliCompatibilityPolicy = {
  readonly policy_id: typeof CLI_COMPATIBILITY_POLICY_ID;
  readonly policy_version: typeof CLI_COMPATIBILITY_POLICY_VERSION;
  readonly extension_version: typeof COMPATIBILITY_EXTENSION_VERSION;
  readonly supported_major: typeof COMPATIBILITY_SUPPORTED_MAJOR;
  readonly minimum_cli: typeof COMPATIBILITY_MINIMUM_CLI;
  readonly maximum_cli_major: typeof COMPATIBILITY_MAXIMUM_CLI_MAJOR;
  readonly allow_prerelease: false;
  readonly allow_unknown: false;
  readonly allow_invalid: false;
  readonly future_major_supported: false;
  readonly compatibility_authority: "extension";
  readonly engine_authority: "assessment_only";
  readonly limitations: readonly string[];
};

export const DEFAULT_CLI_COMPATIBILITY_LIMITATIONS: readonly string[] = [
  "matrix_covers_extension_0_2_0_cli_0_2_x",
  "future_matrix_expansion_possible",
  "no_full_extension_host_ui_automation",
  "marketplace_complete_via_13_12_13_13",
  "worktree_uncommitted",
] as const;

export function createCliCompatibilityPolicy(
  limitations: readonly string[] = DEFAULT_CLI_COMPATIBILITY_LIMITATIONS
): CliCompatibilityPolicy {
  return {
    policy_id: CLI_COMPATIBILITY_POLICY_ID,
    policy_version: CLI_COMPATIBILITY_POLICY_VERSION,
    extension_version: COMPATIBILITY_EXTENSION_VERSION,
    supported_major: COMPATIBILITY_SUPPORTED_MAJOR,
    minimum_cli: COMPATIBILITY_MINIMUM_CLI,
    maximum_cli_major: COMPATIBILITY_MAXIMUM_CLI_MAJOR,
    allow_prerelease: false,
    allow_unknown: false,
    allow_invalid: false,
    future_major_supported: false,
    compatibility_authority: "extension",
    engine_authority: "assessment_only",
    limitations: [...limitations].sort(),
  };
}

export function cliCompatibilityPolicyToStableDict(
  policy: CliCompatibilityPolicy
): Record<string, unknown> {
  return {
    allow_invalid: policy.allow_invalid,
    allow_prerelease: policy.allow_prerelease,
    allow_unknown: policy.allow_unknown,
    compatibility_authority: policy.compatibility_authority,
    engine_authority: policy.engine_authority,
    extension_version: policy.extension_version,
    future_major_supported: policy.future_major_supported,
    limitations: [...policy.limitations].sort(),
    maximum_cli_major: policy.maximum_cli_major,
    minimum_cli: policy.minimum_cli,
    policy_id: policy.policy_id,
    policy_version: policy.policy_version,
    supported_major: policy.supported_major,
  };
}
