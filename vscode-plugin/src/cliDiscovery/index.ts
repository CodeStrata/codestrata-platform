/** CodeStrata CLI discovery contract (Slice 13.2). */

export {
  CLI_DISCOVERY_POLICY_ID,
  CLI_DISCOVERY_POLICY_VERSION,
  DEFAULT_DISCOVERY_LIMITATIONS,
  DEFAULT_PROBE_TIMEOUT_SECONDS,
  createCliDiscoveryPolicy,
  cliDiscoveryPolicyToStableDict,
  type CliDiscoveryPolicy,
} from "./policy";

export {
  CLI_CANDIDATE_SOURCES,
  CANDIDATE_SOURCE_PRECEDENCE,
  isCliCandidateSource,
  type CliCandidateSource,
} from "./sources";

export {
  parseSemanticVersion,
  compareSemanticVersion,
  formatSemanticVersion,
  semanticVersionToStableDict,
  type SemanticVersion,
} from "./versions";

export {
  PRODUCT_IDENTITY_TOKEN,
  parseProductIdentityOutput,
  type IdentityParseResult,
} from "./identity";

export {
  EXTENSION_MAJOR_FOR_DISCOVERY,
  MIN_DISCOVERY_CLI_VERSION,
  classifyDiscoveryCompatibility,
  isProvisionallyCompatible,
  type CompatibilityCategory,
} from "./compatibility";

export {
  CLI_DISCOVERY_STATUSES,
  cliDiscoveryResultToStableDict,
  type CliDiscoveryStatus,
  type CliDiscoveryResult,
  type ResolvedCodeStrataCli,
  type CliDiscoveryOutcome,
} from "./results";

export {
  CLI_DISCOVERY_ERROR_CATEGORIES,
  workflowErrorForDiscoveryStatus,
  type CliDiscoveryErrorCategory,
} from "./errors";

export {
  validateExplicitExecutable,
  isPathStyleCandidate,
  type ExecutableValidationStatus,
  type ExecutableValidationResult,
} from "./executableValidation";

export {
  DEFAULT_CLI_COMMAND_NAME,
  listDiscoveryCandidates,
  type DiscoveryCandidate,
  type ListCandidatesInput,
} from "./candidates";

export {
  VERSION_PROBE_ARGS,
  buildProbeEnvironment,
  defaultProbeLimits,
  type ProbeRunner,
  type ProbeRunRequest,
  type ProbeRunResponse,
  type ProbeLimits,
} from "./probe";

export {
  discoverCodeStrataCli,
  discoveryOutputMessage,
  type DiscoverCodeStrataCliInput,
} from "./discovery";

export {
  discoveryDiagnosticsFromResult,
  discoveryDiagnosticsToStableDict,
  discoveryDiagnosticsContainForbiddenKeys,
  type CliDiscoveryDiagnostics,
} from "./diagnostics";

export { createNodeProbeRunner } from "./nodeProbeRunner";
