import type { MetricId, MetricResult } from "../metrics/metricResult";

export interface PublishedReportRow {
  repository_id?: string;
  portfolio_id?: string;
  report_type: string;
  current_public_url: string | null;
  previous_public_url: string | null;
  current_status: string | null;
  previous_status: string | null;
  last_verified_status?: unknown;
}

export interface PublishedReportsRegistry {
  assessments: PublishedReportRow[];
  engineering_intelligence: PublishedReportRow[];
  source?: string;
  note?: string;
}

export interface InsightsApiClient {
  getOverview(): Promise<MetricResult[]>;
  getMetric(metricId: MetricId | string): Promise<MetricResult>;
  getPublishedReports(): Promise<PublishedReportsRegistry>;
}

export class UnavailableInsightsApiClient implements InsightsApiClient {
  async getOverview(): Promise<MetricResult[]> {
    return [];
  }

  async getMetric(metricId: MetricId | string): Promise<MetricResult> {
    return unavailableResult(metricId);
  }

  async getPublishedReports(): Promise<PublishedReportsRegistry> {
    return { assessments: [], engineering_intelligence: [] };
  }
}

export function unavailableResult(metricId: string): MetricResult {
  return {
    metric_id: metricId,
    status: "error",
    window: {
      start_date_utc: "1970-01-01",
      end_date_utc: "1970-01-01",
      horizon: "bounded_period",
    },
    value: null,
    groups: [],
    completeness: "unavailable",
    denominator: null,
    share: null,
    limitations: ["source_unavailable", "no_live_dashboard_data_claim"],
  };
}

/** Synthetic mocks for tests/dev only — never production default. */
export class MockInsightsApiClient implements InsightsApiClient {
  constructor(private readonly results: MetricResult[]) {}

  async getOverview(): Promise<MetricResult[]> {
    return this.results;
  }

  async getMetric(metricId: MetricId | string): Promise<MetricResult> {
    return (
      this.results.find((r) => r.metric_id === metricId) ??
      unavailableResult(metricId)
    );
  }

  async getPublishedReports(): Promise<PublishedReportsRegistry> {
    return { assessments: [], engineering_intelligence: [] };
  }
}
