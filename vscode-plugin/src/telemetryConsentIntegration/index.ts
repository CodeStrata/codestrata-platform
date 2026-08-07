/** Slice 13.9 telemetry consent integration public exports. */

export {
  TELEMETRY_INTEGRATION_POLICY_ID,
  TELEMETRY_INTEGRATION_POLICY_VERSION,
  TELEMETRY_RUNTIME_POLICY_REF,
  DEFAULT_TELEMETRY_INTEGRATION_LIMITATIONS,
  createTelemetryIntegrationPolicy,
  telemetryIntegrationPolicyToStableDict,
  type TelemetryIntegrationPolicy,
} from "./policy";

export {
  INTEGRATION_OPERATIONS,
  ELIGIBLE_INTEGRATION_OPERATIONS,
  COMMAND_TO_INTEGRATION_OPERATION,
  RECOVERY_ACTIONS_TELEMETRY_INELIGIBLE,
  operationForCommandId,
  isTelemetryEligibleOperation,
  isTelemetryEligibleCommand,
  eligibilityMapToStableDict,
  type IntegrationOperation,
  type EligibleIntegrationOperation,
} from "./eligibility";

export {
  READINESS_STAGES,
  evaluateConsentOrdering,
  consentOrderingToStableDict,
  readinessStageOrder,
  type ReadinessStage,
  type ProductReadinessSnapshot,
  type ConsentOrderingResult,
} from "./ordering";

export {
  createIntegrationDiagnostics,
  integrationDiagnosticsToStableDict,
  integrationDiagnosticsContainForbiddenKeys,
  type TelemetryIntegrationDiagnostics,
} from "./diagnostics";

export {
  assertConsentMayProceed,
  assertFreshConsentDecision,
  integrationOperationLabel,
  TelemetryConsentIntegrationError,
} from "./assert";
