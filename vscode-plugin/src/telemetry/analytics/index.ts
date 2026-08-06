/**
 * VS Code anonymous analytics (Epic 10 Slice 10.7).
 * Local construction only. No HTTP. No persistence. Identity-free.
 */

export {
  assertVsCodeAnalyticsSchemaCompatible,
  compatibleVsCodeAnalyticsSchemaVersions,
  migrateVsCodeAnalyticsMapping,
} from "./compatibility";
export { isAnalyticsConstructionAllowed } from "./consent";
export {
  analyticsDiagnosticsToStableDict,
  emptyVsCodeAnalyticsDiagnostics,
  type VsCodeAnalyticsDiagnostics,
} from "./diagnostics";
export {
  analyticsEventToIntakeDict,
  assertEligibleAnalyticsCommand,
  buildVsCodeAnalyticsEvent,
  buildVsCodeAnalyticsInput,
  classifyDurationBucketMs,
  classifyReleaseAdoption,
  isEligibleAnalyticsCommand,
  mapCommandIdToAnalyticsOperation,
  operationCategoryFromAiFlag,
  validateExtensionVersion,
  type VsCodeAnalyticsEvent,
  type VsCodeAnalyticsInput,
} from "./events";
export { VsCodeAnalyticsError, type VsCodeAnalyticsErrorCode } from "./errors";
export {
  analyticsPolicyAssertsLocalOnly,
  createAnalyticsConstructionSession,
  recordAnalyticsCompleted,
  recordAnalyticsInvoked,
  type AnalyticsConstructionSession,
} from "./isolation";
export {
  describeEngineAnalyticsCatalogMapping,
  type EngineAnalyticsCatalogNote,
} from "./catalogMapping";
export {
  analyticsPreviewToStableJson,
  buildVsCodeAnalyticsPreview,
  type VsCodeAnalyticsPreview,
} from "./preview";
export {
  projectVsCodeAnalyticsEvent,
  projectVsCodeAnalyticsFromMapping,
  type VsCodeAnalyticsProjection,
} from "./projection";
export {
  analyticsPolicyToStableDict,
  COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_POLICY_URN,
  COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_SCHEMA_URN,
  COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_POLICY_VERSION,
  COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_SCHEMA_VERSION,
  defaultVsCodeAnonymousAnalyticsPolicy,
  type VsCodeAnonymousAnalyticsPolicy,
} from "./runtimePolicy";
export {
  APPROVED_ANALYTICS_DURATION_BUCKETS,
  APPROVED_ANALYTICS_FIELD_NAMES,
  APPROVED_ANALYTICS_LIFECYCLES,
  APPROVED_ANALYTICS_OPERATION_CATEGORIES,
  APPROVED_ANALYTICS_OUTCOMES,
  APPROVED_ANALYTICS_RELEASE_ADOPTIONS,
  FORBIDDEN_ANALYTICS_FIELD_NAMES,
  VSCODE_ANALYTICS_CLIENT_NAME,
  VSCODE_ANALYTICS_EDITOR,
} from "./schema";
export {
  analyticsDiagnosticsToStableJson,
  analyticsEventToStableDict,
  analyticsEventToStableJson,
  analyticsPolicyToStableJson,
  analyticsProjectionToStableJson,
} from "./serialization";
export type {
  VsCodeAnalyticsSink,
  VsCodeAnalyticsSinkResult,
} from "./sink";
export { CaptureVsCodeAnalyticsSink } from "./captureSink";
export {
  UnavailableVsCodeAnalyticsSink,
  defaultUnavailableAnalyticsSink,
} from "./unavailableSink";
export { validateVsCodeAnalyticsEvent } from "./validation";
