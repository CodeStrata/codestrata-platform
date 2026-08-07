/**
 * Permanent CLI–extension compatibility matrix (Slice 13.11).
 * Extension 0.2.0 ↔ CLI 0.2.x only.
 */

import {
  parseSemanticVersion,
  type SemanticVersion,
} from "../cliDiscovery/versions";
import {
  COMPATIBILITY_EXTENSION_VERSION,
  COMPATIBILITY_MAXIMUM_CLI_MAJOR,
  COMPATIBILITY_MINIMUM_CLI,
  COMPATIBILITY_SUPPORTED_MAJOR,
  createCliCompatibilityPolicy,
  type CliCompatibilityPolicy,
} from "./policy";

export const COMPATIBILITY_VERDICTS = [
  "supported",
  "upgrade_cli",
  "downgrade_cli",
  "unsupported_major",
  "unsupported_prerelease",
  "invalid_version",
  "unknown_version",
] as const;

export type CompatibilityVerdict = (typeof COMPATIBILITY_VERDICTS)[number];

export const COMPATIBILITY_ERROR_CATEGORIES = [
  "cli_version_too_old",
  "cli_version_too_new",
  "unsupported_major",
  "unsupported_prerelease",
  "invalid_cli_version",
  "unknown_cli_version",
  "unsupported_extension_cli_pair",
  "compatibility_verification_failed",
] as const;

export type CompatibilityErrorCategory =
  (typeof COMPATIBILITY_ERROR_CATEGORIES)[number];

export const COMPATIBILITY_RECOVERY_ACTIONS = [
  "upgrade_cli",
  "install_supported_cli",
  "reinstall_cli",
  "review_installation",
  "none",
] as const;

export type CompatibilityRecoveryAction =
  (typeof COMPATIBILITY_RECOVERY_ACTIONS)[number];

export type CompatibilityDecision = {
  readonly verdict: CompatibilityVerdict;
  readonly extension_version: string;
  readonly cli_version_available: boolean;
  readonly supported: boolean;
  readonly error_category: CompatibilityErrorCategory | "none";
  readonly recovery_action: CompatibilityRecoveryAction;
  readonly workflow_may_continue: boolean;
  readonly telemetry_allowed: false;
  readonly analytics_allowed: false;
  readonly assessment_allowed: boolean;
  readonly limitations: readonly string[];
};

const MIN_CLI = parseSemanticVersion(COMPATIBILITY_MINIMUM_CLI)!;
/** Supported line is extension minor: 0.2.x */
const SUPPORTED_MINOR = MIN_CLI.minor;

export function evaluateCliCompatibility(options: {
  readonly cliVersion?: SemanticVersion | string | undefined;
  readonly extensionVersion?: string;
  readonly policy?: CliCompatibilityPolicy;
}): CompatibilityDecision {
  const policy = options.policy ?? createCliCompatibilityPolicy();
  const extensionVersion =
    options.extensionVersion ?? COMPATIBILITY_EXTENSION_VERSION;
  const limitations = [...policy.limitations].sort();

  const parsed =
    typeof options.cliVersion === "string"
      ? parseSemanticVersion(options.cliVersion)
      : options.cliVersion;

  if (options.cliVersion === undefined || options.cliVersion === "") {
    return decide("unknown_version", extensionVersion, false, limitations);
  }
  if (!parsed) {
    return decide("invalid_version", extensionVersion, false, limitations);
  }
  if (parsed.prerelease) {
    return decide(
      "unsupported_prerelease",
      extensionVersion,
      true,
      limitations
    );
  }
  if (
    parsed.major !== COMPATIBILITY_SUPPORTED_MAJOR ||
    parsed.major > COMPATIBILITY_MAXIMUM_CLI_MAJOR
  ) {
    return decide("unsupported_major", extensionVersion, true, limitations);
  }
  if (parsed.minor < SUPPORTED_MINOR) {
    return decide("upgrade_cli", extensionVersion, true, limitations);
  }
  if (parsed.minor > SUPPORTED_MINOR) {
    return decide("downgrade_cli", extensionVersion, true, limitations);
  }
  // major 0, minor 2, no prerelease — any patch
  return decide("supported", extensionVersion, true, limitations);
}

function decide(
  verdict: CompatibilityVerdict,
  extensionVersion: string,
  cliVersionAvailable: boolean,
  limitations: readonly string[]
): CompatibilityDecision {
  const supported = verdict === "supported";
  return {
    verdict,
    extension_version: extensionVersion,
    cli_version_available: cliVersionAvailable,
    supported,
    error_category: errorForVerdict(verdict),
    recovery_action: recoveryForVerdict(verdict),
    workflow_may_continue: supported,
    telemetry_allowed: false,
    analytics_allowed: false,
    assessment_allowed: supported,
    limitations,
  };
}

function errorForVerdict(
  verdict: CompatibilityVerdict
): CompatibilityErrorCategory | "none" {
  switch (verdict) {
    case "supported":
      return "none";
    case "upgrade_cli":
      return "cli_version_too_old";
    case "downgrade_cli":
      return "cli_version_too_new";
    case "unsupported_major":
      return "unsupported_major";
    case "unsupported_prerelease":
      return "unsupported_prerelease";
    case "invalid_version":
      return "invalid_cli_version";
    case "unknown_version":
      return "unknown_cli_version";
    default:
      return "compatibility_verification_failed";
  }
}

function recoveryForVerdict(
  verdict: CompatibilityVerdict
): CompatibilityRecoveryAction {
  switch (verdict) {
    case "supported":
      return "none";
    case "upgrade_cli":
      return "upgrade_cli";
    case "downgrade_cli":
    case "unsupported_major":
    case "unsupported_prerelease":
      return "install_supported_cli";
    case "invalid_version":
    case "unknown_version":
      return "review_installation";
    default:
      return "reinstall_cli";
  }
}

export function compatibilityDecisionToStableDict(
  decision: CompatibilityDecision
): Record<string, unknown> {
  return {
    analytics_allowed: decision.analytics_allowed,
    assessment_allowed: decision.assessment_allowed,
    cli_version_available: decision.cli_version_available,
    error_category: decision.error_category,
    extension_version: decision.extension_version,
    limitations: [...decision.limitations].sort(),
    recovery_action: decision.recovery_action,
    supported: decision.supported,
    telemetry_allowed: decision.telemetry_allowed,
    verdict: decision.verdict,
    workflow_may_continue: decision.workflow_may_continue,
  };
}

/** Doctor-facing bounded label (no paths/stdout). */
export function doctorCompatibilityLabel(
  verdict: CompatibilityVerdict
): string {
  switch (verdict) {
    case "supported":
      return "Compatible";
    case "upgrade_cli":
      return "Upgrade Required";
    case "downgrade_cli":
    case "unsupported_major":
    case "unsupported_prerelease":
      return "Unsupported Version";
    case "invalid_version":
    case "unknown_version":
      return "Invalid Version";
    default:
      return "Unsupported Version";
  }
}

export function userMessageForCompatibility(
  decision: CompatibilityDecision
): string {
  switch (decision.verdict) {
    case "supported":
      return "CodeStrata Engine CLI is compatible with this extension.";
    case "upgrade_cli":
      return "CodeStrata Engine CLI is too old. Upgrade to a supported 0.2.x CLI.";
    case "downgrade_cli":
      return "CodeStrata Engine CLI is newer than this extension supports. Install a supported 0.2.x CLI.";
    case "unsupported_major":
      return "CodeStrata Engine CLI major version is unsupported by this extension.";
    case "unsupported_prerelease":
      return "Prerelease CodeStrata Engine CLI versions are not supported.";
    case "invalid_version":
      return "CodeStrata Engine CLI version is invalid.";
    case "unknown_version":
      return "CodeStrata Engine CLI version could not be determined.";
    default:
      return "CodeStrata Engine CLI compatibility could not be verified.";
  }
}
