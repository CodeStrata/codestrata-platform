/** Privacy-safe repository initialization diagnostics (Slice 13.4). */

import { REPO_INIT_POLICY_VERSION } from "./policy";
import type { RepoInitResultStatus } from "./results";
import type { RepositoryInitState } from "./states";

export type RepositoryInitializationDiagnostics = {
  readonly initialization_policy_version: typeof REPO_INIT_POLICY_VERSION;
  readonly prior_state: RepositoryInitState;
  readonly terminal_status: RepoInitResultStatus;
  readonly engine_invocation_count: number;
  readonly config_created: boolean;
  readonly existing_config_preserved: boolean;
  readonly post_init_verified: boolean;
  readonly cancelled: boolean;
  readonly source_mutation_detected: false;
  readonly telemetry_invoked: false;
  readonly analytics_invoked: false;
  readonly assessment_invoked: false;
  readonly limitation_codes: readonly string[];
};

export function repositoryInitializationDiagnosticsToStableDict(
  diag: RepositoryInitializationDiagnostics
): Record<string, unknown> {
  return {
    analytics_invoked: diag.analytics_invoked,
    assessment_invoked: diag.assessment_invoked,
    cancelled: diag.cancelled,
    config_created: diag.config_created,
    engine_invocation_count: diag.engine_invocation_count,
    existing_config_preserved: diag.existing_config_preserved,
    initialization_policy_version: diag.initialization_policy_version,
    limitation_codes: [...diag.limitation_codes].sort(),
    post_init_verified: diag.post_init_verified,
    prior_state: diag.prior_state,
    source_mutation_detected: diag.source_mutation_detected,
    telemetry_invoked: diag.telemetry_invoked,
    terminal_status: diag.terminal_status,
  };
}

const FORBIDDEN_KEYS = [
  "workspace_path",
  "config_path",
  "cli_path",
  "executable_path",
  "stdout",
  "stderr",
  "environment",
  "config_contents",
  "source",
] as const;

export function repoInitDiagnosticsContainForbiddenKeys(
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
