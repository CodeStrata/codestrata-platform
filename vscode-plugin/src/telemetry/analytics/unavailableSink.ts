/**
 * Default unavailable VS Code analytics sink (Epic 10 Slice 10.7).
 * No HTTP, endpoint, filesystem, queue, retry, or worker.
 */

import type { VsCodeAnalyticsProjection } from "./projection";
import type { VsCodeAnalyticsSink, VsCodeAnalyticsSinkResult } from "./sink";

export class UnavailableVsCodeAnalyticsSink implements VsCodeAnalyticsSink {
  readonly sinkCategory = "unavailable" as const;

  send(_event: VsCodeAnalyticsProjection): VsCodeAnalyticsSinkResult {
    return { kind: "unavailable" };
  }
}

export function defaultUnavailableAnalyticsSink(): UnavailableVsCodeAnalyticsSink {
  return new UnavailableVsCodeAnalyticsSink();
}
