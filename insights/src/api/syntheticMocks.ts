import type { MetricResult } from "../metrics/metricResult";
import { V02_OVERVIEW_METRIC_IDS } from "../dashboard/labels";

const WINDOW = {
  start_date_utc: "2026-07-10",
  end_date_utc: "2026-08-08",
  horizon: "bounded_period",
} as const;

/** Clearly synthetic MetricResults for component tests — not live data. */
export const SYNTHETIC_MOCK_RESULTS: MetricResult[] = [
  {
    metric_id: "github_stars",
    status: "ok",
    window: { ...WINDOW, horizon: "external" },
    value: 42,
    groups: [],
    completeness: "complete",
    denominator: null,
    share: null,
    limitations: ["github_public_api"],
  },
  {
    metric_id: "github_forks",
    status: "ok",
    window: { ...WINDOW, horizon: "external" },
    value: 7,
    groups: [],
    completeness: "complete",
    denominator: null,
    share: null,
    limitations: ["github_public_api"],
  },
  {
    metric_id: "community_sentiment",
    status: "ok",
    window: { ...WINDOW, horizon: "external" },
    value: null,
    groups: [],
    completeness: "complete",
    denominator: 0,
    share: null,
    limitations: ["no_responses_yet", "voluntary_feedback_only", "explicit_yes_no_only"],
  },
  {
    metric_id: "total_assessments",
    status: "ok",
    window: WINDOW,
    value: 12,
    groups: [],
    completeness: "complete",
    denominator: null,
    share: null,
    limitations: [],
  },
  {
    metric_id: "first_assessments",
    status: "ok",
    window: { ...WINDOW, horizon: "retention_window" },
    value: 8,
    groups: [],
    completeness: "complete",
    denominator: null,
    share: null,
    limitations: ["first_repeat_retention_only"],
  },
  {
    metric_id: "repeat_assessments",
    status: "ok",
    window: { ...WINDOW, horizon: "retention_window" },
    value: 4,
    groups: [],
    completeness: "complete",
    denominator: null,
    share: null,
    limitations: ["first_repeat_retention_only"],
  },
  {
    metric_id: "successful_assessments",
    status: "ok",
    window: WINDOW,
    value: 10,
    groups: [],
    completeness: "complete",
    denominator: null,
    share: null,
    limitations: [],
  },
  {
    metric_id: "failed_assessments",
    status: "ok",
    window: WINDOW,
    value: 2,
    groups: [],
    completeness: "complete",
    denominator: null,
    share: null,
    limitations: [],
  },
  {
    metric_id: "published_reports",
    status: "ok",
    window: { ...WINDOW, horizon: "external" },
    value: 3,
    groups: [],
    completeness: "complete",
    denominator: null,
    share: null,
    limitations: ["report_artifact_store_registry"],
  },
];

export function assertSyntheticCoversV02Overview(): void {
  const ids = new Set(SYNTHETIC_MOCK_RESULTS.map((r) => r.metric_id));
  for (const id of V02_OVERVIEW_METRIC_IDS) {
    if (!ids.has(id)) {
      throw new Error(`synthetic mock missing ${id}`);
    }
  }
}
