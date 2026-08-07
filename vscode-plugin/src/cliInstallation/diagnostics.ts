/** Privacy-safe installation-guidance diagnostics (Slice 13.3). */

import type { CliDiscoveryStatus } from "../cliDiscovery/results";
import { CLI_INSTALLATION_POLICY_VERSION } from "./policy";
import type {
  GuidanceCategory,
  InstallationGuidanceStatus,
} from "./results";

export type InstallationDiagnostics = {
  readonly installation_policy_version: typeof CLI_INSTALLATION_POLICY_VERSION;
  readonly approach: "guidance_only";
  readonly discovery_status: CliDiscoveryStatus | "not_attempted";
  readonly guidance_status: InstallationGuidanceStatus;
  readonly method_category: string;
  readonly user_action_required: boolean;
  readonly rediscovery_attempted: boolean;
  readonly rediscovery_outcome: "not_attempted" | "succeeded" | "failed";
  readonly guidance_category: GuidanceCategory;
  readonly limitation_codes: readonly string[];
};

export function installationDiagnosticsToStableDict(
  diag: InstallationDiagnostics
): Record<string, unknown> {
  return {
    approach: diag.approach,
    discovery_status: diag.discovery_status,
    guidance_category: diag.guidance_category,
    guidance_status: diag.guidance_status,
    installation_policy_version: diag.installation_policy_version,
    limitation_codes: [...diag.limitation_codes].sort(),
    method_category: diag.method_category,
    rediscovery_attempted: diag.rediscovery_attempted,
    rediscovery_outcome: diag.rediscovery_outcome,
    user_action_required: diag.user_action_required,
  };
}

const FORBIDDEN_KEYS = [
  "command",
  "command_text",
  "url",
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
] as const;

export function installationDiagnosticsContainForbiddenKeys(
  blob: Record<string, unknown>
): string[] {
  const hits: string[] = [];
  for (const key of FORBIDDEN_KEYS) {
    if (key in blob) {
      hits.push(key);
    }
  }
  const text = JSON.stringify(blob);
  if (
    text.includes("/Users/") ||
    text.includes("/home/") ||
    text.includes("https://") ||
    text.includes("pip install")
  ) {
    hits.push("sensitive_value");
  }
  return hits;
}
