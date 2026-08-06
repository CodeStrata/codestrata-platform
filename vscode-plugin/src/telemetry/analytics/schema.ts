/**
 * VS Code anonymous analytics schema tokens (Epic 10 Slice 10.7).
 */

export {
  COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_SCHEMA_ID,
  COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_SCHEMA_URN,
  COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_SCHEMA_VERSION,
} from "./runtimePolicy";

export const VSCODE_ANALYTICS_CLIENT_NAME = "vscode_extension" as const;
export const VSCODE_ANALYTICS_EDITOR = "vscode" as const;

export type VsCodeAnalyticsOperationCategory = "assess" | "assess_with_ai";
export type VsCodeAnalyticsLifecycle =
  | "feature_invoked"
  | "feature_completed"
  | "operation_failed";
export type VsCodeAnalyticsOutcome = "success" | "failure" | "cancelled";
export type VsCodeAnalyticsDurationBucket =
  | "lt_1s"
  | "s_1_10"
  | "s_10_60"
  | "m_1_5"
  | "gt_5m"
  | "unknown";
export type VsCodeAnalyticsReleaseAdoption =
  | "stable"
  | "prerelease"
  | "development"
  | "unknown";
export type VsCodeAnalyticsFailureCategory =
  | "cli_unavailable"
  | "cli_incompatible"
  | "command_failed"
  | "report_unavailable"
  | "cancelled"
  | "internal_failure";

export const APPROVED_ANALYTICS_OPERATION_CATEGORIES: readonly VsCodeAnalyticsOperationCategory[] =
  ["assess", "assess_with_ai"];

export const APPROVED_ANALYTICS_LIFECYCLES: readonly VsCodeAnalyticsLifecycle[] = [
  "feature_invoked",
  "feature_completed",
  "operation_failed",
];

export const APPROVED_ANALYTICS_OUTCOMES: readonly VsCodeAnalyticsOutcome[] = [
  "success",
  "failure",
  "cancelled",
];

export const APPROVED_ANALYTICS_DURATION_BUCKETS: readonly VsCodeAnalyticsDurationBucket[] =
  ["lt_1s", "s_1_10", "s_10_60", "m_1_5", "gt_5m", "unknown"];

export const APPROVED_ANALYTICS_RELEASE_ADOPTIONS: readonly VsCodeAnalyticsReleaseAdoption[] =
  ["stable", "prerelease", "development", "unknown"];

export const APPROVED_ANALYTICS_FAILURE_CATEGORIES: readonly VsCodeAnalyticsFailureCategory[] =
  [
    "cli_unavailable",
    "cli_incompatible",
    "command_failed",
    "report_unavailable",
    "cancelled",
    "internal_failure",
  ];

/** Allowlisted serialized field names for analytics projection. */
export const APPROVED_ANALYTICS_FIELD_NAMES = [
  "ai_used",
  "client_name",
  "duration_bucket",
  "editor",
  "extension_version",
  "failure_category",
  "lifecycle",
  "limitations",
  "operation_category",
  "outcome",
  "policy_version",
  "release_adoption",
  "schema_id",
  "schema_version",
  "telemetry_event_schema_version",
  "telemetry_runtime_policy_version",
] as const;

export const FORBIDDEN_ANALYTICS_FIELD_NAMES = [
  "installation_id",
  "event_id",
  "machine_id",
  "machineId",
  "telemetry_session_id",
  "telemetrySessionId",
  "workspace",
  "workspace_uri",
  "workspaceUri",
  "repository",
  "repository_url",
  "project",
  "organization",
  "customer",
  "account",
  "user",
  "email",
  "hostname",
  "ip",
  "document",
  "document_uri",
  "file",
  "path",
  "cwd",
  "extension_path",
  "storage_uri",
  "argv",
  "command_line",
  "raw_command_id",
  "command_id",
  "stdout",
  "stderr",
  "output_text",
  "report_path",
  "finding",
  "evidence",
  "recommendation",
  "source",
  "source_code",
  "exception",
  "traceback",
  "environment",
  "credential",
  "secret",
  "api_key",
  "authorization",
  "prompt",
  "response",
  "provider",
  "model_id",
  "token_count",
  "cost",
  "exact_duration",
  "duration_ms",
  "timestamp",
] as const;
