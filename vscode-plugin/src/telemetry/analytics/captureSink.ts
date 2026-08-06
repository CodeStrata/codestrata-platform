/**
 * Test-only capture analytics sink (Epic 10 Slice 10.7).
 * Not a production default.
 */

import type { VsCodeAnalyticsProjection } from "./projection";
import type {
  VsCodeAnalyticsSink,
  VsCodeAnalyticsSinkResult,
  VsCodeAnalyticsSinkResultKind,
} from "./sink";

export class CaptureVsCodeAnalyticsSink implements VsCodeAnalyticsSink {
  readonly sinkCategory = "capture" as const;
  readonly captured: VsCodeAnalyticsProjection[] = [];

  constructor(
    private readonly resultKind: VsCodeAnalyticsSinkResultKind = "captured",
    private readonly raiseOnSend = false
  ) {}

  send(event: VsCodeAnalyticsProjection): VsCodeAnalyticsSinkResult {
    if (this.raiseOnSend) {
      throw new Error("capture_analytics_sink_simulated_failure");
    }
    this.captured.push(event);
    return { kind: this.resultKind };
  }

  clear(): void {
    this.captured.length = 0;
  }
}
