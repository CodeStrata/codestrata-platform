/**
 * Deterministic serialization for VS Code analytics (Epic 10 Slice 10.7).
 */

import {
  analyticsPolicyToStableDict,
  type VsCodeAnonymousAnalyticsPolicy,
} from "./runtimePolicy";
import {
  analyticsEventToIntakeDict,
  type VsCodeAnalyticsEvent,
} from "./events";
import type { VsCodeAnalyticsProjection } from "./projection";
import type { VsCodeAnalyticsDiagnostics } from "./diagnostics";
import { analyticsDiagnosticsToStableDict } from "./diagnostics";

function stableJson(value: Record<string, unknown>): string {
  return JSON.stringify(value, Object.keys(value).sort());
}

export function analyticsPolicyToStableJson(
  policy: VsCodeAnonymousAnalyticsPolicy
): string {
  return stableJson(analyticsPolicyToStableDict(policy));
}

export function analyticsEventToStableDict(
  event: VsCodeAnalyticsEvent
): Record<string, unknown> {
  const intake = analyticsEventToIntakeDict(event);
  const sorted: Record<string, unknown> = {};
  for (const key of Object.keys(intake).sort()) {
    sorted[key] = intake[key];
  }
  return sorted;
}

export function analyticsEventToStableJson(event: VsCodeAnalyticsEvent): string {
  return stableJson(analyticsEventToStableDict(event));
}

export function analyticsProjectionToStableJson(
  projection: VsCodeAnalyticsProjection
): string {
  return stableJson({ ...projection.fields });
}

export function analyticsDiagnosticsToStableJson(
  diagnostics: VsCodeAnalyticsDiagnostics
): string {
  return stableJson(analyticsDiagnosticsToStableDict(diagnostics));
}
