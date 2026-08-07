/** Privacy-safe CLI discovery diagnostics (no paths / PATH / stdout). */

import { CLI_DISCOVERY_POLICY_VERSION } from "./policy";
import type { CliDiscoveryResult } from "./results";

export type CliDiscoveryDiagnostics = {
  readonly discovery_policy_version: typeof CLI_DISCOVERY_POLICY_VERSION;
  readonly status: CliDiscoveryResult["status"];
  readonly candidate_source: CliDiscoveryResult["candidate_source"];
  readonly product_identity_valid: boolean;
  readonly version_present: boolean;
  readonly version_major?: number;
  readonly version_minor?: number;
  readonly version_patch?: number;
  readonly compatibility_category: CliDiscoveryResult["compatibility_category"];
  readonly executable_available: boolean;
  readonly probe_attempted: boolean;
  readonly probe_timed_out: boolean;
  readonly limitation_codes: readonly string[];
};

export function discoveryDiagnosticsFromResult(
  result: CliDiscoveryResult
): CliDiscoveryDiagnostics {
  return {
    discovery_policy_version: CLI_DISCOVERY_POLICY_VERSION,
    status: result.status,
    candidate_source: result.candidate_source,
    product_identity_valid: result.product_identity_valid,
    version_present: result.version_present,
    version_major: result.version_major,
    version_minor: result.version_minor,
    version_patch: result.version_patch,
    compatibility_category: result.compatibility_category,
    executable_available: result.executable_available,
    probe_attempted: result.probe_attempted,
    probe_timed_out: result.probe_timed_out,
    limitation_codes: result.limitations,
  };
}

export function discoveryDiagnosticsToStableDict(
  diag: CliDiscoveryDiagnostics
): Record<string, unknown> {
  const out: Record<string, unknown> = {
    candidate_source: diag.candidate_source,
    compatibility_category: diag.compatibility_category,
    discovery_policy_version: diag.discovery_policy_version,
    executable_available: diag.executable_available,
    limitation_codes: [...diag.limitation_codes].sort(),
    probe_attempted: diag.probe_attempted,
    probe_timed_out: diag.probe_timed_out,
    product_identity_valid: diag.product_identity_valid,
    status: diag.status,
    version_present: diag.version_present,
  };
  if (diag.version_major !== undefined) {
    out.version_major = diag.version_major;
  }
  if (diag.version_minor !== undefined) {
    out.version_minor = diag.version_minor;
  }
  if (diag.version_patch !== undefined) {
    out.version_patch = diag.version_patch;
  }
  return out;
}

const FORBIDDEN_KEYS = [
  "executable_path",
  "cli_path",
  "path",
  "PATH",
  "stdout",
  "stderr",
  "environment",
  "home",
  "username",
  "workspace_path",
  "command",
] as const;

export function discoveryDiagnosticsContainForbiddenKeys(
  blob: Record<string, unknown>
): string[] {
  const hits: string[] = [];
  for (const key of FORBIDDEN_KEYS) {
    if (key in blob) {
      hits.push(key);
    }
  }
  const text = JSON.stringify(blob);
  if (text.includes("/Users/") || text.includes("/home/") || text.includes("C:\\\\")) {
    hits.push("absolute_path_value");
  }
  return hits;
}
