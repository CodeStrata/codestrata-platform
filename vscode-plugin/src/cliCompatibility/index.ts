/** Slice 13.11 CLI–extension compatibility public exports. */

export {
  CLI_COMPATIBILITY_POLICY_ID,
  CLI_COMPATIBILITY_POLICY_VERSION,
  COMPATIBILITY_EXTENSION_VERSION,
  COMPATIBILITY_SUPPORTED_MAJOR,
  COMPATIBILITY_MINIMUM_CLI,
  COMPATIBILITY_MAXIMUM_CLI_MAJOR,
  DEFAULT_CLI_COMPATIBILITY_LIMITATIONS,
  createCliCompatibilityPolicy,
  cliCompatibilityPolicyToStableDict,
  type CliCompatibilityPolicy,
} from "./policy";

export {
  COMPATIBILITY_VERDICTS,
  COMPATIBILITY_ERROR_CATEGORIES,
  COMPATIBILITY_RECOVERY_ACTIONS,
  evaluateCliCompatibility,
  compatibilityDecisionToStableDict,
  doctorCompatibilityLabel,
  userMessageForCompatibility,
  type CompatibilityVerdict,
  type CompatibilityErrorCategory,
  type CompatibilityRecoveryAction,
  type CompatibilityDecision,
} from "./matrix";

export {
  diagnosticsFromCompatibilityDecision,
  cliCompatibilityDiagnosticsToStableDict,
  compatibilityDiagnosticsContainForbiddenKeys,
  type CliCompatibilityDiagnostics,
} from "./diagnostics";
