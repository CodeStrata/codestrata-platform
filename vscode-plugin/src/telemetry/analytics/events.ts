/**
 * VS Code anonymous analytics models (Epic 10 Slice 10.7).
 * Identity-free. No workspace/repository/document/path/argv/output.
 */

import {
  COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_POLICY_VERSION,
  COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_SCHEMA_ID,
  COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_SCHEMA_VERSION,
  defaultVsCodeAnonymousAnalyticsPolicy,
} from "./runtimePolicy";
import {
  APPROVED_ANALYTICS_DURATION_BUCKETS,
  APPROVED_ANALYTICS_FAILURE_CATEGORIES,
  APPROVED_ANALYTICS_LIFECYCLES,
  APPROVED_ANALYTICS_OPERATION_CATEGORIES,
  APPROVED_ANALYTICS_OUTCOMES,
  APPROVED_ANALYTICS_RELEASE_ADOPTIONS,
  VSCODE_ANALYTICS_CLIENT_NAME,
  VSCODE_ANALYTICS_EDITOR,
  type VsCodeAnalyticsDurationBucket,
  type VsCodeAnalyticsFailureCategory,
  type VsCodeAnalyticsLifecycle,
  type VsCodeAnalyticsOperationCategory,
  type VsCodeAnalyticsOutcome,
  type VsCodeAnalyticsReleaseAdoption,
} from "./schema";
import { VsCodeAnalyticsError } from "./errors";
import {
  ELIGIBLE_TELEMETRY_COMMANDS,
  type EligibleTelemetryCommand,
} from "../promptPolicy";

const MAX_EXTENSION_VERSION_LENGTH = 32;
const SEMVER_LIKE_RE =
  /^[0-9]+(?:\.[0-9]+){0,3}(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$/;

export type VsCodeAnalyticsInput = {
  readonly operationCategory: VsCodeAnalyticsOperationCategory;
  readonly lifecycle: VsCodeAnalyticsLifecycle;
  readonly extensionVersion: string;
  readonly releaseAdoption: VsCodeAnalyticsReleaseAdoption;
  readonly aiUsed: boolean;
  readonly outcome?: VsCodeAnalyticsOutcome;
  readonly durationBucket?: VsCodeAnalyticsDurationBucket;
  readonly failureCategory?: VsCodeAnalyticsFailureCategory;
};

export type VsCodeAnalyticsEvent = {
  readonly schemaId: typeof COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_SCHEMA_ID;
  readonly schemaVersion: typeof COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_SCHEMA_VERSION;
  readonly policyVersion: typeof COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_POLICY_VERSION;
  readonly telemetryRuntimePolicyVersion: "1.0";
  readonly telemetryEventSchemaVersion: "1.0";
  readonly clientName: typeof VSCODE_ANALYTICS_CLIENT_NAME;
  readonly editor: typeof VSCODE_ANALYTICS_EDITOR;
  readonly extensionVersion: string;
  readonly operationCategory: VsCodeAnalyticsOperationCategory;
  readonly lifecycle: VsCodeAnalyticsLifecycle;
  readonly outcome?: VsCodeAnalyticsOutcome;
  readonly durationBucket?: VsCodeAnalyticsDurationBucket;
  readonly aiUsed: boolean;
  readonly releaseAdoption: VsCodeAnalyticsReleaseAdoption;
  readonly failureCategory?: VsCodeAnalyticsFailureCategory;
  readonly limitations: readonly string[];
};

export function mapCommandIdToAnalyticsOperation(
  commandId: string
): VsCodeAnalyticsOperationCategory {
  if (commandId === "codestrata.assess") {
    return "assess";
  }
  if (commandId === "codestrata.assessWithAi") {
    return "assess_with_ai";
  }
  throw new VsCodeAnalyticsError("invalid_operation_category");
}

export function operationCategoryFromAiFlag(
  aiUsed: boolean
): VsCodeAnalyticsOperationCategory {
  return aiUsed ? "assess_with_ai" : "assess";
}

export function isEligibleAnalyticsCommand(commandId: string): boolean {
  return (ELIGIBLE_TELEMETRY_COMMANDS as readonly string[]).includes(commandId);
}

export function assertEligibleAnalyticsCommand(
  commandId: string
): asserts commandId is EligibleTelemetryCommand {
  if (!isEligibleAnalyticsCommand(commandId)) {
    throw new VsCodeAnalyticsError("invalid_operation_category");
  }
}

export function validateExtensionVersion(version: string): string {
  if (
    typeof version !== "string" ||
    !version ||
    version.length > MAX_EXTENSION_VERSION_LENGTH
  ) {
    throw new VsCodeAnalyticsError("invalid_extension_version");
  }
  if (
    version.includes("/") ||
    version.includes("\\") ||
    version.includes("://") ||
    version.includes("\n") ||
    version.includes("\r")
  ) {
    throw new VsCodeAnalyticsError("invalid_extension_version");
  }
  if (!SEMVER_LIKE_RE.test(version)) {
    throw new VsCodeAnalyticsError("invalid_extension_version");
  }
  return version;
}

/**
 * Bounded release-adoption classifier without Marketplace / network checks.
 *
 * Uses only the injected extension version string:
 * - development: 0.x or contains "dev"
 * - prerelease: pre-release label (alpha/beta/rc/pre)
 * - stable: otherwise valid semver-like
 * - unknown: never guessed from remote catalogs
 */
export function classifyReleaseAdoption(
  extensionVersion: string
): VsCodeAnalyticsReleaseAdoption {
  const version = validateExtensionVersion(extensionVersion);
  const lower = version.toLowerCase();
  if (lower.includes("dev")) {
    return "development";
  }
  if (/^0\./.test(version)) {
    return "development";
  }
  if (/-/.test(version) && /(alpha|beta|rc|pre)/.test(lower)) {
    return "prerelease";
  }
  if (/-/.test(version)) {
    return "prerelease";
  }
  return "stable";
}

export function classifyDurationBucketMs(
  durationMs: number | undefined | null
): VsCodeAnalyticsDurationBucket {
  if (durationMs === undefined || durationMs === null) {
    return "unknown";
  }
  if (typeof durationMs !== "number" || !Number.isFinite(durationMs) || durationMs < 0) {
    return "unknown";
  }
  if (durationMs < 1_000) {
    return "lt_1s";
  }
  if (durationMs < 10_000) {
    return "s_1_10";
  }
  if (durationMs < 60_000) {
    return "s_10_60";
  }
  if (durationMs < 300_000) {
    return "m_1_5";
  }
  return "gt_5m";
}

export function buildVsCodeAnalyticsInput(
  options: VsCodeAnalyticsInput
): VsCodeAnalyticsInput {
  if (
    !(APPROVED_ANALYTICS_OPERATION_CATEGORIES as readonly string[]).includes(
      options.operationCategory
    )
  ) {
    throw new VsCodeAnalyticsError("invalid_operation_category");
  }
  if (!(APPROVED_ANALYTICS_LIFECYCLES as readonly string[]).includes(options.lifecycle)) {
    throw new VsCodeAnalyticsError("invalid_lifecycle");
  }
  const extensionVersion = validateExtensionVersion(options.extensionVersion);
  if (
    !(APPROVED_ANALYTICS_RELEASE_ADOPTIONS as readonly string[]).includes(
      options.releaseAdoption
    )
  ) {
    throw new VsCodeAnalyticsError("invalid_release_adoption");
  }
  if (typeof options.aiUsed !== "boolean") {
    throw new VsCodeAnalyticsError("internal");
  }

  // AI boolean must match operation category.
  if (options.operationCategory === "assess_with_ai" && options.aiUsed !== true) {
    throw new VsCodeAnalyticsError("internal");
  }
  if (options.operationCategory === "assess" && options.aiUsed !== false) {
    throw new VsCodeAnalyticsError("internal");
  }

  if (options.lifecycle === "feature_invoked") {
    if (options.outcome !== undefined || options.failureCategory !== undefined) {
      throw new VsCodeAnalyticsError("outcome_failure_mismatch");
    }
  } else {
    if (
      options.outcome === undefined ||
      !(APPROVED_ANALYTICS_OUTCOMES as readonly string[]).includes(options.outcome)
    ) {
      throw new VsCodeAnalyticsError("invalid_outcome");
    }
    if (options.outcome === "success") {
      if (options.failureCategory !== undefined) {
        throw new VsCodeAnalyticsError("outcome_failure_mismatch");
      }
    } else if (options.failureCategory !== undefined) {
      if (
        !(APPROVED_ANALYTICS_FAILURE_CATEGORIES as readonly string[]).includes(
          options.failureCategory
        )
      ) {
        throw new VsCodeAnalyticsError("invalid_failure_category");
      }
    }
  }

  if (
    options.durationBucket !== undefined &&
    !(APPROVED_ANALYTICS_DURATION_BUCKETS as readonly string[]).includes(
      options.durationBucket
    )
  ) {
    throw new VsCodeAnalyticsError("invalid_duration_bucket");
  }

  return {
    operationCategory: options.operationCategory,
    lifecycle: options.lifecycle,
    extensionVersion,
    releaseAdoption: options.releaseAdoption,
    aiUsed: options.aiUsed,
    outcome: options.outcome,
    durationBucket: options.durationBucket,
    failureCategory: options.failureCategory,
  };
}

export function buildVsCodeAnalyticsEvent(
  input: VsCodeAnalyticsInput
): VsCodeAnalyticsEvent {
  const validated = buildVsCodeAnalyticsInput(input);
  const policy = defaultVsCodeAnonymousAnalyticsPolicy();
  return {
    schemaId: COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_SCHEMA_ID,
    schemaVersion: COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_SCHEMA_VERSION,
    policyVersion: COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_POLICY_VERSION,
    telemetryRuntimePolicyVersion: "1.0",
    telemetryEventSchemaVersion: "1.0",
    clientName: VSCODE_ANALYTICS_CLIENT_NAME,
    editor: VSCODE_ANALYTICS_EDITOR,
    extensionVersion: validated.extensionVersion,
    operationCategory: validated.operationCategory,
    lifecycle: validated.lifecycle,
    outcome: validated.outcome,
    durationBucket: validated.durationBucket,
    aiUsed: validated.aiUsed,
    releaseAdoption: validated.releaseAdoption,
    failureCategory: validated.failureCategory,
    limitations: policy.limitations,
  };
}

export function analyticsEventToIntakeDict(
  event: VsCodeAnalyticsEvent
): Record<string, unknown> {
  const payload: Record<string, unknown> = {
    ai_used: event.aiUsed,
    client_name: event.clientName,
    editor: event.editor,
    extension_version: event.extensionVersion,
    lifecycle: event.lifecycle,
    limitations: [...event.limitations],
    operation_category: event.operationCategory,
    policy_version: event.policyVersion,
    release_adoption: event.releaseAdoption,
    schema_id: event.schemaId,
    schema_version: event.schemaVersion,
    telemetry_event_schema_version: event.telemetryEventSchemaVersion,
    telemetry_runtime_policy_version: event.telemetryRuntimePolicyVersion,
  };
  if (event.outcome !== undefined) {
    payload.outcome = event.outcome;
  }
  if (event.durationBucket !== undefined) {
    payload.duration_bucket = event.durationBucket;
  }
  if (event.failureCategory !== undefined) {
    payload.failure_category = event.failureCategory;
  }
  return payload;
}
