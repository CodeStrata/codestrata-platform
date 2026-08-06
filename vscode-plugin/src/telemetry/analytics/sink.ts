/**
 * Analytics sink contract (Epic 10 Slice 10.7).
 */

import type { VsCodeAnalyticsProjection } from "./projection";

export type VsCodeAnalyticsSinkResultKind = "unavailable" | "captured" | "dropped";

export type VsCodeAnalyticsSinkResult = {
  readonly kind: VsCodeAnalyticsSinkResultKind;
};

export type VsCodeAnalyticsSink = {
  readonly sinkCategory: "unavailable" | "capture";
  send(event: VsCodeAnalyticsProjection): VsCodeAnalyticsSinkResult;
};
