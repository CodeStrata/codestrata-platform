/** Privacy-safe CLI compatibility diagnostics (Slice 13.11). */

import { CLI_COMPATIBILITY_POLICY_VERSION } from "./policy";
import type { CompatibilityDecision } from "./matrix";

export type CliCompatibilityDiagnostics = {
  readonly compatibility_policy_version: typeof CLI_COMPATIBILITY_POLICY_VERSION;
  readonly operation: "evaluate_compatibility";
  readonly extension_version: string;
  readonly verdict: string;
  readonly supported: boolean;
  readonly workflow_may_continue: boolean;
  readonly assessment_allowed: boolean;
  readonly telemetry_allowed: false;
  readonly analytics_allowed: false;
  readonly probe_count: 0;
  readonly limitations: readonly string[];
};

const FORBIDDEN_KEYS = [
  "path",
  "uri",
  "workspace",
  "stdout",
  "stderr",
  "environment",
  "credential",
  "provider",
  "machineId",
  "timestamp",
] as const;

export function diagnosticsFromCompatibilityDecision(
  decision: CompatibilityDecision
): CliCompatibilityDiagnostics {
  return {
    compatibility_policy_version: CLI_COMPATIBILITY_POLICY_VERSION,
    operation: "evaluate_compatibility",
    extension_version: decision.extension_version,
    verdict: decision.verdict,
    supported: decision.supported,
    workflow_may_continue: decision.workflow_may_continue,
    assessment_allowed: decision.assessment_allowed,
    telemetry_allowed: false,
    analytics_allowed: false,
    probe_count: 0,
    limitations: [...decision.limitations].sort(),
  };
}

export function cliCompatibilityDiagnosticsToStableDict(
  diagnostics: CliCompatibilityDiagnostics
): Record<string, unknown> {
  return {
    analytics_allowed: diagnostics.analytics_allowed,
    assessment_allowed: diagnostics.assessment_allowed,
    compatibility_policy_version: diagnostics.compatibility_policy_version,
    extension_version: diagnostics.extension_version,
    limitations: [...diagnostics.limitations].sort(),
    operation: diagnostics.operation,
    probe_count: diagnostics.probe_count,
    supported: diagnostics.supported,
    telemetry_allowed: diagnostics.telemetry_allowed,
    verdict: diagnostics.verdict,
    workflow_may_continue: diagnostics.workflow_may_continue,
  };
}

export function compatibilityDiagnosticsContainForbiddenKeys(
  value: Record<string, unknown>
): boolean {
  const blob = JSON.stringify(value).toLowerCase();
  if (blob.includes("/users/") || blob.includes("file://")) {
    return true;
  }
  for (const key of FORBIDDEN_KEYS) {
    if (Object.prototype.hasOwnProperty.call(value, key)) {
      return true;
    }
  }
  return false;
}
