/** Installation guidance request / result / recovery models (Slice 13.3). */

import type { CliDiscoveryStatus } from "../cliDiscovery/results";
import { DEFAULT_INSTALLATION_LIMITATIONS } from "./policy";

export const INSTALLATION_OPERATIONS = [
  "show_guidance",
  "copy_install_command",
  "open_terminal",
  "open_documentation",
  "refresh_detection",
] as const;

export type InstallationOperation = (typeof INSTALLATION_OPERATIONS)[number];

/** Public command ID mapped to show_guidance. */
export const INSTALL_ENGINE_COMMAND_ID = "codestrata.installEngine" as const;

export const INSTALLATION_GUIDANCE_STATUSES = [
  "not_required",
  "guidance_available",
  "unsupported_platform",
  "installation_method_unavailable",
  "user_cancelled",
  "action_opened",
  "command_copied",
  "terminal_opened",
  "rediscovery_succeeded",
  "rediscovery_failed",
] as const;

export type InstallationGuidanceStatus =
  (typeof INSTALLATION_GUIDANCE_STATUSES)[number];

export const GUIDANCE_CATEGORIES = [
  "none",
  "install_cli",
  "correct_cli_setting",
  "make_cli_executable",
  "replace_non_codestrata_executable",
  "install_supported_version",
  "retry_discovery",
  "view_documentation",
] as const;

export type GuidanceCategory = (typeof GUIDANCE_CATEGORIES)[number];

export const RECOVERY_CATEGORIES = GUIDANCE_CATEGORIES;

export type RecoveryCategory = GuidanceCategory;

export type InstallationGuidanceResult = {
  readonly status: InstallationGuidanceStatus;
  readonly discovery_status: CliDiscoveryStatus | "not_attempted";
  readonly guidance_category: GuidanceCategory;
  readonly supported_method_count: number;
  readonly user_action_required: boolean;
  readonly rediscovery_available: boolean;
  readonly rediscovery_attempted: boolean;
  readonly rediscovery_outcome: "not_attempted" | "succeeded" | "failed";
  readonly recovery_category: RecoveryCategory;
  readonly limitations: readonly string[];
};

export function installationGuidanceResultToStableDict(
  result: InstallationGuidanceResult
): Record<string, unknown> {
  return {
    discovery_status: result.discovery_status,
    guidance_category: result.guidance_category,
    limitations: [...result.limitations].sort(),
    rediscovery_attempted: result.rediscovery_attempted,
    rediscovery_available: result.rediscovery_available,
    rediscovery_outcome: result.rediscovery_outcome,
    recovery_category: result.recovery_category,
    status: result.status,
    supported_method_count: result.supported_method_count,
    user_action_required: result.user_action_required,
  };
}

export function mapDiscoveryToGuidanceCategory(
  discoveryStatus: CliDiscoveryStatus | "not_attempted"
): GuidanceCategory {
  switch (discoveryStatus) {
    case "compatible":
      return "none";
    case "invalid_configuration":
    case "not_executable":
      return "correct_cli_setting";
    case "identity_mismatch":
      return "replace_non_codestrata_executable";
    case "incompatible":
      return "install_supported_version";
    case "probe_failed":
    case "probe_timed_out":
    case "malformed_version":
    case "version_unavailable":
      return "retry_discovery";
    case "not_found":
    default:
      return "install_cli";
  }
}

export function guidanceNotRequired(
  discoveryStatus: CliDiscoveryStatus = "compatible"
): InstallationGuidanceResult {
  return {
    status: "not_required",
    discovery_status: discoveryStatus,
    guidance_category: "none",
    supported_method_count: 0,
    user_action_required: false,
    rediscovery_available: true,
    rediscovery_attempted: false,
    rediscovery_outcome: "not_attempted",
    recovery_category: "none",
    limitations: [...DEFAULT_INSTALLATION_LIMITATIONS].sort(),
  };
}

export const INSTALLATION_ERROR_CATEGORIES = [
  "installation_not_required",
  "installation_method_unavailable",
  "unsupported_platform",
  "guidance_unavailable",
  "clipboard_failed",
  "terminal_open_failed",
  "documentation_open_failed",
  "automatic_installation_forbidden",
  "user_cancelled",
  "rediscovery_failed",
  "unsafe_install_command",
  "installation_internal_error",
] as const;

export type InstallationErrorCategory =
  (typeof INSTALLATION_ERROR_CATEGORIES)[number];
