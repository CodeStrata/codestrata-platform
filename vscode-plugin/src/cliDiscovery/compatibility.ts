/**
 * Discovery compatibility bridge (Slice 13.11).
 * Discovery finds/probes CLI; permanent matrix lives in cliCompatibility.
 */

import { evaluateCliCompatibility } from "../cliCompatibility";
import type { SemanticVersion } from "./versions";

export {
  COMPATIBILITY_EXTENSION_VERSION as EXTENSION_VERSION_FOR_COMPATIBILITY,
  COMPATIBILITY_MINIMUM_CLI,
} from "../cliCompatibility";

export const EXTENSION_MAJOR_FOR_DISCOVERY = 0 as const;

export type CompatibilityCategory =
  | "compatible"
  | "incompatible_major"
  | "incompatible_below_minimum"
  | "incompatible_above_supported"
  | "incompatible_prerelease"
  | "version_unavailable"
  | "invalid_version";

export function classifyDiscoveryCompatibility(
  version: SemanticVersion | undefined
): CompatibilityCategory {
  const decision = evaluateCliCompatibility({ cliVersion: version });
  switch (decision.verdict) {
    case "supported":
      return "compatible";
    case "upgrade_cli":
      return "incompatible_below_minimum";
    case "downgrade_cli":
      return "incompatible_above_supported";
    case "unsupported_major":
      return "incompatible_major";
    case "unsupported_prerelease":
      return "incompatible_prerelease";
    case "invalid_version":
      return "invalid_version";
    case "unknown_version":
    default:
      return "version_unavailable";
  }
}

export function isProvisionallyCompatible(
  version: SemanticVersion | undefined
): boolean {
  return classifyDiscoveryCompatibility(version) === "compatible";
}
