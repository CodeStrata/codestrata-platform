/**
 * Privacy-first VS Code telemetry runtime (Slice 9.13)
 * with anonymous analytics construction (Slice 10.7).
 */

export {
  allowForSession,
  consentFromPreference,
  consentToStableDict,
  defaultConsent,
  denyForSession,
  nonInteractiveDisabledConsent,
  readPreferenceState,
  TELEMETRY_PREFERENCE_STATE_KEY,
  writePreferenceState,
  type TelemetryPreferenceState,
  type VsCodeTelemetryConsent,
  type VsCodeTelemetryDecision,
  type VsCodeTelemetryDecisionSource,
} from "./consent";
export {
  createDiagnostics,
  diagnosticsToStableDict,
  type VsCodeTelemetryDiagnostics,
} from "./diagnostics";
export {
  APPROVED_EVENT_TYPES,
  APPROVED_FIELD_NAMES,
  VSCODE_CLIENT_NAME,
  createAssessCompletedEvent,
  createAssessInvokedEvent,
  eventToIntakeDict,
  type VsCodeRuntimeTelemetryEvent,
} from "./events";
export {
  describeEngineCatalogMapping,
  vscodeEventTypesSubsetOfEngineCatalog,
} from "./catalogMapping";
export {
  createIsolationSession,
  isolationAnalyticsDiagnostics,
  isolationDiagnosticsBlob,
  runCommandWithTelemetryIsolation,
  type CommandOutcome,
  type IsolationSession,
} from "./isolation";
export {
  buildVsCodeTelemetryPreview,
  previewToStableJson,
} from "./preview";
export {
  evaluatePromptEligibility,
  ELIGIBLE_TELEMETRY_COMMANDS,
  EXCLUDED_TELEMETRY_COMMANDS,
  isEligibleTelemetryCommand,
} from "./promptPolicy";
export {
  preferenceLabel,
  runTelemetryConsentPrompt,
  type TelemetryPreferenceStore,
  type TelemetryPromptResult,
  type TelemetryPromptUi,
} from "./prompt";
export {
  TELEMETRY_ALLOW_LABEL,
  TELEMETRY_CONSENT_MESSAGE,
  TELEMETRY_DENY_LABEL,
  TELEMETRY_LEARN_MORE_LABEL,
  TELEMETRY_UPGRADE_ALLOW_LABEL,
  TELEMETRY_UPGRADE_DENY_LABEL,
  TELEMETRY_UPGRADE_MESSAGE,
  preferenceLabelFromEngineState,
  resolveCanonicalConsentForAssessment,
  type CanonicalConsentGateResult,
} from "./canonicalConsent";
export {
  projectRuntimeEvent,
  privacySafeToStableJson,
  TelemetryProjectionError,
  type PrivacySafeVsCodeTelemetryEvent,
} from "./projection";
export {
  COMMUNITY_VSCODE_TELEMETRY_RUNTIME_POLICY_URN,
  defaultVsCodeTelemetryRuntimePolicy,
  policyToStableDict,
} from "./runtimePolicy";
export type {
  ExtensionTelemetryTransport,
  TelemetryTransportResult,
} from "./transport";
export { CaptureExtensionTelemetryTransport } from "./captureTransport";
export {
  UnavailableExtensionTelemetryTransport,
  defaultUnavailableTransport,
} from "./unavailableTransport";

// Slice 10.7 anonymous analytics (local construction; unavailable sink).
export {
  APPROVED_ANALYTICS_FIELD_NAMES,
  APPROVED_ANALYTICS_OPERATION_CATEGORIES,
  CaptureVsCodeAnalyticsSink,
  COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_POLICY_URN,
  COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_SCHEMA_URN,
  FORBIDDEN_ANALYTICS_FIELD_NAMES,
  UnavailableVsCodeAnalyticsSink,
  VSCODE_ANALYTICS_CLIENT_NAME,
  analyticsEventToStableJson,
  analyticsPolicyToStableDict,
  analyticsPolicyToStableJson,
  analyticsPreviewToStableJson,
  analyticsProjectionToStableJson,
  assertVsCodeAnalyticsSchemaCompatible,
  buildVsCodeAnalyticsEvent,
  buildVsCodeAnalyticsInput,
  buildVsCodeAnalyticsPreview,
  classifyDurationBucketMs,
  classifyReleaseAdoption,
  compatibleVsCodeAnalyticsSchemaVersions,
  createAnalyticsConstructionSession,
  defaultUnavailableAnalyticsSink,
  defaultVsCodeAnonymousAnalyticsPolicy,
  describeEngineAnalyticsCatalogMapping,
  emptyVsCodeAnalyticsDiagnostics,
  isAnalyticsConstructionAllowed,
  isEligibleAnalyticsCommand,
  mapCommandIdToAnalyticsOperation,
  projectVsCodeAnalyticsEvent,
  projectVsCodeAnalyticsFromMapping,
  recordAnalyticsCompleted,
  recordAnalyticsInvoked,
  validateExtensionVersion,
  validateVsCodeAnalyticsEvent,
  VsCodeAnalyticsError,
} from "./analytics";
