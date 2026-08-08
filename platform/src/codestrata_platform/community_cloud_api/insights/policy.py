"""Static aggregation policy constants (SDK-free)."""

from __future__ import annotations

COMMUNITY_INSIGHTS_AGGREGATION_POLICY_ID = "community-insights-aggregation-policy"
COMMUNITY_INSIGHTS_AGGREGATION_POLICY_VERSION = "1.0"

MINIMUM_GROUP_COUNT = 3
SUPPRESSED_GROUP_LABEL = "other_suppressed"
CACHE_MODE = "none"
CHECKPOINT_MODE = "retention_only_with_limitation"

SUPPORTED_METRICS: frozenset[str] = frozenset(
    {
        "total_anonymous_installations",
        "daily_active_installations",
        "monthly_active_installations",
        "first_assessments",
        "repeat_assessments",
        "successful_assessments",
        "failed_assessments",
        "cli_version_adoption",
        "assessment_head_usage",
        "language_ecosystem_distribution",
        "ai_provider_adoption",
        "ai_model_adoption",
        "vscode_extension_usage",
        "release_adoption",
        "validation_dataset_growth",
    }
)

METRIC_HORIZONS: dict[str, str] = {
    "total_anonymous_installations": "retention_window",
    "daily_active_installations": "daily",
    "monthly_active_installations": "rolling_30_day",
    "first_assessments": "retention_window",
    "repeat_assessments": "retention_window",
    "successful_assessments": "bounded_period",
    "failed_assessments": "bounded_period",
    "cli_version_adoption": "bounded_period",
    "assessment_head_usage": "bounded_period",
    "language_ecosystem_distribution": "bounded_period",
    "ai_provider_adoption": "bounded_period",
    "ai_model_adoption": "bounded_period",
    "vscode_extension_usage": "bounded_period",
    "release_adoption": "bounded_period",
    "validation_dataset_growth": "external",
}

APPROVED_TELEMETRY_TYPES: frozenset[str] = frozenset(
    {
        "feature_invoked",
        "feature_completed",
        "application_started",
        "application_completed",
        "operation_failed",
    }
)

APPROVED_CLI_OPS: frozenset[str] = frozenset({"assess", "assess_with_ai"})
APPROVED_EXTENSION_OPS: frozenset[str] = frozenset({"assess", "assess_with_ai"})

SUCCESS_STATUSES: frozenset[str] = frozenset({"completed", "partially_completed"})
SUCCESS_RESULTS: frozenset[str] = frozenset({"succeeded", "partially_succeeded"})
FAILED_STATUSES: frozenset[str] = frozenset({"failed"})
FAILED_RESULTS: frozenset[str] = frozenset({"failed"})
CANCELLED_STATUSES: frozenset[str] = frozenset({"cancelled"})
CANCELLED_RESULTS: frozenset[str] = frozenset({"cancelled"})

PROVIDER_ADOPTION_FAMILIES: frozenset[str] = frozenset(
    {"aws_bedrock", "openai", "openrouter"}
)
PROVIDER_UNAVAILABLE = "unavailable"

ALLOWED_PRIMARY_LANGUAGES: frozenset[str] = frozenset(
    {
        "python",
        "java",
        "javascript",
        "typescript",
        "go",
        "csharp",
        "rust",
        "unknown",
        "unavailable",
    }
)

ALLOWED_PACKAGE_ECOSYSTEMS: frozenset[str] = frozenset(
    {
        "maven",
        "gradle",
        "npm",
        "python",
        "nuget",
        "composer",
        "cargo",
        "mixed",
        "unknown",
        "unavailable",
    }
)

ALLOWED_MODEL_FAMILIES: frozenset[str] = frozenset(
    {
        "amazon_nova_family",
        "gpt_family",
        "other_supported",
        "unavailable",
    }
)

ALLOWED_ASSESSMENT_HEADS: frozenset[str] = frozenset(
    {
        "technology_inventory",
        "architecture",
        "technical_debt",
        "dependency",
        "security",
        "testing",
        "cloud_readiness",
        "ai_readiness",
        "performance",
        "modernization",
    }
)

BOUNDED_LIMITATIONS: frozenset[str] = frozenset(
    {
        "optional_identity_undercount",
        "retention_window_limited",
        "suppressed_small_groups",
        "malformed_objects_omitted",
        "query_budget_reached",
        "source_unavailable",
        "first_repeat_retention_only",
        "validation_growth_snapshots_unavailable",
        "production_ingestion_still_unwired",
        "no_live_dashboard_data_claim",
    }
)

DEFAULT_OVERVIEW_METRICS: tuple[str, ...] = (
    "total_anonymous_installations",
    "daily_active_installations",
    "monthly_active_installations",
    "first_assessments",
    "repeat_assessments",
    "successful_assessments",
    "failed_assessments",
    "cli_version_adoption",
    "assessment_head_usage",
    "language_ecosystem_distribution",
    "ai_provider_adoption",
    "ai_model_adoption",
    "vscode_extension_usage",
    "release_adoption",
    "validation_dataset_growth",
)

# Streams that can share a single bounded read for overview batching.
BATCH_STREAM_GROUPS: dict[str, tuple[str, ...]] = {
    "assessment_metadata": (
        "first_assessments",
        "repeat_assessments",
        "successful_assessments",
        "failed_assessments",
        "assessment_head_usage",
        "language_ecosystem_distribution",
    ),
    "multi_activity": (
        "total_anonymous_installations",
        "daily_active_installations",
        "monthly_active_installations",
    ),
    "cli_event": ("cli_version_adoption",),
    "extension_event": ("vscode_extension_usage",),
    "release": ("release_adoption",),
    "ai_usage": ("ai_provider_adoption", "ai_model_adoption"),
}
