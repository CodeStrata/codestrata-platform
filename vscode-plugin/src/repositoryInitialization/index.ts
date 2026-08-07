/** CodeStrata repository initialization contract (Slice 13.4). */

export {
  REPO_INIT_POLICY_ID,
  REPO_INIT_POLICY_VERSION,
  CODESTRATA_CONFIG_BASENAME,
  DEFAULT_REPO_INIT_LIMITATIONS,
  createRepositoryInitializationPolicy,
  repositoryInitializationPolicyToStableDict,
  type RepositoryInitializationPolicy,
} from "./policy";

export {
  REPOSITORY_INIT_STATES,
  isRepositoryInitState,
  type RepositoryInitState,
} from "./states";

export {
  REPO_INIT_RESULT_STATUSES,
  REPO_INIT_RECOVERY_CATEGORIES,
  REPO_INIT_ERROR_CATEGORIES,
  createRepoInitResult,
  repositoryInitializationResultToStableDict,
  type RepoInitResultStatus,
  type RepoInitRecoveryCategory,
  type RepositoryInitializationResult,
  type RepoInitErrorCategory,
} from "./results";

export {
  resolveConfigPath,
  classifyConfigContents,
  detectRepositoryInitState,
  assertInitArgsForbidForce,
  type DetectInitStateInput,
  type DetectInitStateResult,
} from "./detection";

export {
  planRepositoryInitialization,
  resultForPlanWithoutCli,
  resultAfterEngineInit,
  diagnosticsFromResult,
  userMessageForInitResult,
  recoveryForDiscoveryFailure,
  type InitPlan,
  type InitCliRunResult,
} from "./orchestration";

export {
  repositoryInitializationDiagnosticsToStableDict,
  repoInitDiagnosticsContainForbiddenKeys,
  type RepositoryInitializationDiagnostics,
} from "./diagnostics";
