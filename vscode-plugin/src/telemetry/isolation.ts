/**
 * Fail-silent command isolation for VS Code telemetry (Slice 9.13)
 * with optional local analytics construction (Slice 10.7).
 *
 * Analytics uses the same command-local consent decision. Consent does not
 * enable transport. Default analytics sink is unavailable. Analytics failures
 * never alter primary command results or replace primary errors.
 */

import type { VsCodeTelemetryConsent } from "./consent";
import {
  createDiagnostics,
  diagnosticsToStableDict,
  type VsCodeTelemetryDiagnostics,
} from "./diagnostics";
import {
  createAssessCompletedEvent,
  createAssessInvokedEvent,
  type VsCodeRuntimeTelemetryEvent,
} from "./events";
import { projectRuntimeEvent } from "./projection";
import type { ExtensionTelemetryTransport } from "./transport";
import { defaultUnavailableTransport } from "./unavailableTransport";
import {
  createAnalyticsConstructionSession,
  recordAnalyticsCompleted,
  recordAnalyticsInvoked,
  type AnalyticsConstructionSession,
} from "./analytics/isolation";
import type { VsCodeAnalyticsSink } from "./analytics/sink";
import { defaultUnavailableAnalyticsSink } from "./analytics/unavailableSink";
import type { VsCodeAnalyticsDiagnostics } from "./analytics/diagnostics";

export type IsolationSession = {
  readonly consent: VsCodeTelemetryConsent;
  readonly transport: ExtensionTelemetryTransport;
  readonly diagnostics: VsCodeTelemetryDiagnostics;
  readonly extensionVersion?: string;
  readonly analytics: AnalyticsConstructionSession;
  readonly nowMs?: () => number;
};

export type CommandOutcome = "success" | "failure" | "cancelled";

export function createIsolationSession(options: {
  consent: VsCodeTelemetryConsent;
  transport?: ExtensionTelemetryTransport;
  analyticsSink?: VsCodeAnalyticsSink;
  promptShown?: boolean;
  extensionVersion?: string;
  nowMs?: () => number;
}): IsolationSession {
  const transport = options.transport ?? defaultUnavailableTransport();
  const extensionVersion = options.extensionVersion ?? "0.2.0";
  const analytics = createAnalyticsConstructionSession({
    consent: options.consent,
    extensionVersion,
    sink: options.analyticsSink ?? defaultUnavailableAnalyticsSink(),
    nowMs: options.nowMs,
  });
  return {
    consent: options.consent,
    transport,
    diagnostics: createDiagnostics({
      consent: options.consent,
      transportCategory: transport.transportCategory,
      promptShown: options.promptShown,
    }),
    extensionVersion,
    analytics,
    nowMs: options.nowMs,
  };
}

function recordSafely(
  session: IsolationSession,
  event: VsCodeRuntimeTelemetryEvent
): void {
  const diag = session.diagnostics;
  try {
    diag.eventsSeen += 1;
    const projected = projectRuntimeEvent(event);
    diag.eventsProjected += 1;
    if (!session.consent.transmissionAuthorized) {
      diag.eventsDropped += 1;
      return;
    }
    const result = session.transport.send(projected);
    if (result.kind === "unavailable") {
      diag.transportUnavailable += 1;
    } else if (result.kind === "sent") {
      diag.transportSent += 1;
    } else {
      diag.eventsDropped += 1;
    }
  } catch {
    diag.failures += 1;
  }
}

/**
 * Run a primary command; telemetry/analytics never alters its result or exception.
 *
 * Ordering:
 * 1. feature_invoked telemetry + analytics (consent-gated for analytics)
 * 2. primary command
 * 3. completed/failed telemetry + analytics
 * 4. return primary result unchanged
 */
export async function runCommandWithTelemetryIsolation<T>(options: {
  session: IsolationSession;
  aiUsed: boolean;
  primary: () => Promise<T>;
}): Promise<T> {
  const { session, aiUsed, primary } = options;
  recordSafely(
    session,
    createAssessInvokedEvent({
      aiUsed,
      extensionVersion: session.extensionVersion,
    })
  );
  try {
    recordAnalyticsInvoked(session.analytics, { aiUsed });
  } catch {
    // Fail-silent: analytics must never block the primary command.
  }

  try {
    const result = await primary();
    const outcome = normalizeOutcome(result);
    recordSafely(
      session,
      createAssessCompletedEvent({
        aiUsed,
        success: outcome === "success",
        cancelled: outcome === "cancelled",
        extensionVersion: session.extensionVersion,
      })
    );
    try {
      recordAnalyticsCompleted(session.analytics, {
        aiUsed,
        outcome,
        nowMs: session.nowMs,
      });
    } catch {
      // Fail-silent.
    }
    return result;
  } catch (error) {
    recordSafely(
      session,
      createAssessCompletedEvent({
        aiUsed,
        success: false,
        extensionVersion: session.extensionVersion,
      })
    );
    try {
      recordAnalyticsCompleted(session.analytics, {
        aiUsed,
        outcome: "failure",
        nowMs: session.nowMs,
      });
    } catch {
      // Fail-silent.
    }
    throw error;
  }
}

function normalizeOutcome(result: unknown): CommandOutcome {
  if (result === "success" || result === "failure" || result === "cancelled") {
    return result;
  }
  return "success";
}

export function isolationDiagnosticsBlob(session: IsolationSession): string {
  return JSON.stringify(diagnosticsToStableDict(session.diagnostics));
}

export function isolationAnalyticsDiagnostics(
  session: IsolationSession
): VsCodeAnalyticsDiagnostics {
  return session.analytics.diagnostics;
}
