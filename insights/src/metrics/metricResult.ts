/** MetricResult — synchronized with community-insights-metrics-contract:1.0 */

export type MetricStatus = "ok" | "suppressed" | "error";

export type Completeness =
  | "complete"
  | "partial"
  | "unavailable"
  | "not_applicable";

export type MetricHorizon =
  | "daily"
  | "rolling_30_day"
  | "retention_window"
  | "checkpoint_backed"
  | "external"
  | "bounded_period";

export interface MetricWindow {
  start_date_utc: string;
  end_date_utc: string;
  horizon: MetricHorizon | string;
}

export interface MetricGroup {
  dimension: string;
  key: string;
  count: number;
  share: number | null;
  suppressed: boolean;
}

/**
 * Aggregate-only result. Must never include installation_id, S3 keys,
 * event IDs, raw telemetry, repository/path fields, or exact model_id.
 */
export interface MetricResult {
  metric_id: string;
  status: MetricStatus;
  window: MetricWindow;
  value: number | null;
  groups: MetricGroup[];
  completeness: Completeness;
  denominator: number | null;
  share: number | null;
  limitations: string[];
}

export const FORBIDDEN_METRIC_RESULT_KEYS = [
  "installation_id",
  "installation_ids",
  "raw_events",
  "object_keys",
  "payloads",
  "s3_key",
  "event_id",
  "repository_name",
  "file_path",
  "exact_model_id",
  "model_id",
] as const;

export const SUPPRESSED_GROUP_KEY = "other_suppressed";

export type MetricId =
  | "total_anonymous_installations"
  | "daily_active_installations"
  | "monthly_active_installations"
  | "first_assessments"
  | "repeat_assessments"
  | "successful_assessments"
  | "failed_assessments"
  | "cli_version_adoption"
  | "assessment_head_usage"
  | "language_ecosystem_distribution"
  | "ai_provider_adoption"
  | "ai_model_adoption"
  | "vscode_extension_usage"
  | "release_adoption"
  | "validation_dataset_growth";
