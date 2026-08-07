/** Bounded CLI discovery error taxonomy (Slice 13.2). */

export const CLI_DISCOVERY_ERROR_CATEGORIES = [
  "explicit_candidate_missing",
  "explicit_candidate_not_file",
  "explicit_candidate_not_executable",
  "executable_not_found",
  "identity_probe_failed",
  "identity_mismatch",
  "version_output_missing",
  "version_output_malformed",
  "unsupported_version",
  "probe_timeout",
  "probe_output_exceeded",
  "unsafe_candidate",
  "discovery_internal_error",
] as const;

export type CliDiscoveryErrorCategory =
  (typeof CLI_DISCOVERY_ERROR_CATEGORIES)[number];

/** Map discovery status → workflow error category (bounded). */
export function workflowErrorForDiscoveryStatus(
  status: string
):
  | "cli_unavailable"
  | "cli_incompatible"
  | "cli_probe_failed"
  | "invalid_cli_configuration" {
  switch (status) {
    case "incompatible":
      return "cli_incompatible";
    case "invalid_configuration":
    case "not_executable":
      return "invalid_cli_configuration";
    case "probe_failed":
    case "probe_timed_out":
    case "identity_mismatch":
    case "malformed_version":
    case "version_unavailable":
      return "cli_probe_failed";
    default:
      return "cli_unavailable";
  }
}
