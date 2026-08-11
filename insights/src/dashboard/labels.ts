/** Bounded limitation codes → user-safe copy. Unknown codes omitted (not interpolated). */

export const LIMITATION_COPY: Record<string, string> = {
  retention_window_limited: "Limited to the retention window.",
  optional_identity_undercount:
    "Some events lack installation identity and may undercount.",
  suppressed_small_groups: "Small groups are suppressed for privacy.",
  malformed_objects_omitted: "Some malformed objects were omitted.",
  query_budget_reached: "Query budget reached; results may be partial.",
  source_unavailable: "Source data is not available.",
  first_repeat_retention_only:
    "First/repeat assessment history is retention-window limited.",
  validation_growth_snapshots_unavailable:
    "Historical validation growth is not available yet.",
  production_ingestion_still_unwired:
    "Production analytics ingestion is not enabled.",
  no_live_dashboard_data_claim:
    "This dashboard does not claim live production telemetry.",
  github_public_api: "Loaded from the public GitHub API.",
  report_artifact_store_registry: "Counted from published report registry slots.",
  community_sentiment_not_yet_collected:
    "No voluntary Yes/No responses yet.",
  no_responses_yet: "No voluntary Yes/No responses yet.",
  voluntary_feedback_only: "Based only on explicit Yes/No feedback responses.",
  explicit_yes_no_only: "Explicit Yes/No feedback only — no AI sentiment inference.",
};

export function humanizeLimitations(codes: string[]): string[] {
  const out: string[] = [];
  for (const code of codes) {
    const text = LIMITATION_COPY[code];
    if (text) out.push(text);
  }
  return out;
}

/** v0.2.0 Insights dashboard — nine metrics only. */
export const V02_OVERVIEW_METRIC_IDS = [
  "github_stars",
  "github_forks",
  "community_sentiment",
  "total_assessments",
  "first_assessments",
  "repeat_assessments",
  "successful_assessments",
  "failed_assessments",
  "published_reports",
] as const;

export const METRIC_DISPLAY_NAMES: Record<string, string> = {
  github_stars: "GitHub Stars",
  github_forks: "GitHub Forks",
  community_sentiment: "Community Sentiment",
  total_assessments: "Total Assessments",
  first_assessments: "First Assessments",
  repeat_assessments: "Repeat Assessments",
  successful_assessments: "Successful Assessments",
  failed_assessments: "Failed Assessments",
  published_reports: "Published Reports",
  // retained labels for older API responses / tests
  total_anonymous_installations: "Anonymous installations",
  daily_active_installations: "Daily active installations",
  monthly_active_installations: "30-day active installations",
  cli_version_adoption: "CLI version adoption",
  assessment_head_usage: "Assessment-head usage",
  language_ecosystem_distribution: "Language and ecosystem distribution",
  ai_provider_adoption: "AI provider adoption",
  ai_model_adoption: "AI model family adoption",
  vscode_extension_usage: "VS Code extension usage",
  release_adoption: "Release adoption",
  validation_dataset_growth: "Validation dataset size",
};
