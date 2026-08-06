/**
 * Fail-silent VS Code analytics construction helpers (Epic 10 Slice 10.7).
 */

import type { VsCodeTelemetryConsent } from "../consent";
import { isAnalyticsConstructionAllowed } from "./consent";
import {
  emptyVsCodeAnalyticsDiagnostics,
  type VsCodeAnalyticsDiagnostics,
} from "./diagnostics";
import {
  buildVsCodeAnalyticsEvent,
  classifyDurationBucketMs,
  classifyReleaseAdoption,
  operationCategoryFromAiFlag,
  type VsCodeAnalyticsEvent,
} from "./events";
import { projectVsCodeAnalyticsEvent } from "./projection";
import { defaultVsCodeAnonymousAnalyticsPolicy } from "./runtimePolicy";
import type { VsCodeAnalyticsSink } from "./sink";
import { defaultUnavailableAnalyticsSink } from "./unavailableSink";
import type {
  VsCodeAnalyticsDurationBucket,
  VsCodeAnalyticsFailureCategory,
  VsCodeAnalyticsLifecycle,
  VsCodeAnalyticsOutcome,
} from "./schema";

export type AnalyticsConstructionSession = {
  readonly consent: VsCodeTelemetryConsent;
  readonly sink: VsCodeAnalyticsSink;
  readonly diagnostics: VsCodeAnalyticsDiagnostics;
  readonly extensionVersion: string;
  readonly releaseAdoption: ReturnType<typeof classifyReleaseAdoption>;
  readonly startedAtMs?: number;
};

export function createAnalyticsConstructionSession(options: {
  consent: VsCodeTelemetryConsent;
  extensionVersion: string;
  sink?: VsCodeAnalyticsSink;
  nowMs?: () => number;
}): AnalyticsConstructionSession {
  const sink = options.sink ?? defaultUnavailableAnalyticsSink();
  let releaseAdoption: ReturnType<typeof classifyReleaseAdoption> = "unknown";
  try {
    releaseAdoption = classifyReleaseAdoption(options.extensionVersion);
  } catch {
    releaseAdoption = "unknown";
  }
  return {
    consent: options.consent,
    sink,
    diagnostics: emptyVsCodeAnalyticsDiagnostics(options.consent.decision),
    extensionVersion: options.extensionVersion,
    releaseAdoption,
    startedAtMs: options.nowMs?.(),
  };
}

function recordSafely(
  session: AnalyticsConstructionSession,
  lifecycle: VsCodeAnalyticsLifecycle,
  options: {
    aiUsed: boolean;
    outcome?: VsCodeAnalyticsOutcome;
    failureCategory?: VsCodeAnalyticsFailureCategory;
    durationBucket?: VsCodeAnalyticsDurationBucket;
  }
): void {
  const diag = session.diagnostics;
  diag.attempts += 1;
  if (!isAnalyticsConstructionAllowed(session.consent)) {
    diag.rejected += 1;
    return;
  }
  try {
    const event: VsCodeAnalyticsEvent = buildVsCodeAnalyticsEvent({
      operationCategory: operationCategoryFromAiFlag(options.aiUsed),
      lifecycle,
      extensionVersion: session.extensionVersion,
      releaseAdoption: session.releaseAdoption,
      aiUsed: options.aiUsed,
      outcome: options.outcome,
      durationBucket: options.durationBucket,
      failureCategory: options.failureCategory,
    });
    const projected = projectVsCodeAnalyticsEvent(event);
    diag.projected += 1;
    diag.operationCategory = event.operationCategory;
    diag.lifecycle = event.lifecycle;
    diag.outcome = event.outcome;
    diag.durationBucket = event.durationBucket;
    diag.aiUsed = event.aiUsed;
    diag.releaseAdoption = event.releaseAdoption;
    diag.limitationCodes = [...event.limitations];

    const result = session.sink.send(projected);
    if (result.kind === "unavailable") {
      diag.sunkUnavailable += 1;
    } else if (result.kind === "captured") {
      diag.sunkCaptured += 1;
    }
  } catch {
    diag.rejected += 1;
  }
}

export function recordAnalyticsInvoked(
  session: AnalyticsConstructionSession,
  options: { aiUsed: boolean }
): void {
  recordSafely(session, "feature_invoked", { aiUsed: options.aiUsed });
}

export function recordAnalyticsCompleted(
  session: AnalyticsConstructionSession,
  options: {
    aiUsed: boolean;
    outcome: VsCodeAnalyticsOutcome;
    nowMs?: () => number;
  }
): void {
  let durationBucket: VsCodeAnalyticsDurationBucket | undefined;
  try {
    if (session.startedAtMs !== undefined && options.nowMs) {
      durationBucket = classifyDurationBucketMs(options.nowMs() - session.startedAtMs);
    }
  } catch {
    durationBucket = "unknown";
  }

  let failureCategory: VsCodeAnalyticsFailureCategory | undefined;
  if (options.outcome === "failure") {
    failureCategory = "command_failed";
  } else if (options.outcome === "cancelled") {
    failureCategory = "cancelled";
  }

  const lifecycle =
    options.outcome === "failure" ? "operation_failed" : "feature_completed";

  recordSafely(session, lifecycle, {
    aiUsed: options.aiUsed,
    outcome: options.outcome,
    failureCategory,
    durationBucket,
  });
}

export function analyticsPolicyAssertsLocalOnly(): boolean {
  const policy = defaultVsCodeAnonymousAnalyticsPolicy();
  return (
    policy.localConstructionOnly &&
    !policy.persistenceEnabled &&
    !policy.transmissionEnabled &&
    !policy.installationIdentityAllowed
  );
}
