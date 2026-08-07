/** CodeStrata CLI installation guidance contract (Slice 13.3 Approach A). */

export {
  CLI_INSTALLATION_POLICY_ID,
  CLI_INSTALLATION_POLICY_VERSION,
  DEFAULT_INSTALLATION_LIMITATIONS,
  SUPPORTED_INSTALLATION_METHOD_IDS,
  createCliInstallationPolicy,
  cliInstallationPolicyToStableDict,
  type CliInstallationPolicy,
  type InstallationApproach,
} from "./policy";

export {
  INSTALLATION_METHOD_IDS,
  TRUSTED_INSTALLATION_DOCS_URL,
  TRUSTED_COMMAND_TEMPLATES,
  installationMethodCatalog,
  trustedCommandForMethod,
  methodCatalogToStableDict,
  type InstallationMethodId,
  type InstallationMethod,
  type InstallationActionCategory,
} from "./methods";

export {
  INSTALLATION_OPERATIONS,
  INSTALL_ENGINE_COMMAND_ID,
  INSTALLATION_GUIDANCE_STATUSES,
  GUIDANCE_CATEGORIES,
  RECOVERY_CATEGORIES,
  INSTALLATION_ERROR_CATEGORIES,
  mapDiscoveryToGuidanceCategory,
  guidanceNotRequired,
  installationGuidanceResultToStableDict,
  type InstallationOperation,
  type InstallationGuidanceStatus,
  type GuidanceCategory,
  type RecoveryCategory,
  type InstallationGuidanceResult,
  type InstallationErrorCategory,
} from "./results";

export {
  installationDiagnosticsToStableDict,
  installationDiagnosticsContainForbiddenKeys,
  type InstallationDiagnostics,
} from "./diagnostics";

export {
  runInstallationGuidance,
  detectInstallationPlatform,
  automaticInstallationAllowed,
  type InstallationUiAdapters,
  type RunInstallationGuidanceInput,
  type InstallationPlatform,
} from "./guidance";

// vscodeHost is imported by extension/onboarding only — do not re-export here
// so unit tests can load the domain package without the `vscode` module.
