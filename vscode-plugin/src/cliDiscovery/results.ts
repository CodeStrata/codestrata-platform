/** Typed public CLI discovery results (Slice 13.2). No paths/stdout. */

import type { CompatibilityCategory } from "./compatibility";
import type { CliCandidateSource } from "./sources";

export const CLI_DISCOVERY_STATUSES = [
  "compatible",
  "incompatible",
  "not_found",
  "not_executable",
  "identity_mismatch",
  "version_unavailable",
  "malformed_version",
  "probe_failed",
  "probe_timed_out",
  "invalid_configuration",
] as const;

export type CliDiscoveryStatus = (typeof CLI_DISCOVERY_STATUSES)[number];

export type CliDiscoveryResult = {
  readonly status: CliDiscoveryStatus;
  readonly candidate_source: CliCandidateSource;
  readonly product_identity_valid: boolean;
  readonly version_present: boolean;
  readonly version_major?: number;
  readonly version_minor?: number;
  readonly version_patch?: number;
  readonly compatibility_category: CompatibilityCategory | "not_applicable";
  readonly executable_available: boolean;
  readonly probe_attempted: boolean;
  readonly probe_timed_out: boolean;
  readonly limitations: readonly string[];
};

/** Private runtime handle — never serialize into diagnostics/telemetry. */
export type ResolvedCodeStrataCli = {
  readonly command: string;
  readonly source: CliCandidateSource;
  readonly version: string;
  readonly version_major: number;
  readonly version_minor: number;
  readonly version_patch: number;
};

export type CliDiscoveryOutcome = {
  readonly public: CliDiscoveryResult;
  readonly resolved?: ResolvedCodeStrataCli;
};

export function cliDiscoveryResultToStableDict(
  result: CliDiscoveryResult
): Record<string, unknown> {
  const out: Record<string, unknown> = {
    candidate_source: result.candidate_source,
    compatibility_category: result.compatibility_category,
    executable_available: result.executable_available,
    limitations: [...result.limitations].sort(),
    probe_attempted: result.probe_attempted,
    probe_timed_out: result.probe_timed_out,
    product_identity_valid: result.product_identity_valid,
    status: result.status,
    version_present: result.version_present,
  };
  if (result.version_major !== undefined) {
    out.version_major = result.version_major;
  }
  if (result.version_minor !== undefined) {
    out.version_minor = result.version_minor;
  }
  if (result.version_patch !== undefined) {
    out.version_patch = result.version_patch;
  }
  return out;
}
