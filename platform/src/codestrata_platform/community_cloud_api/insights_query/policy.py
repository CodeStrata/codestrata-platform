"""Static query policy constants (SDK-free)."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.insights_query.models import QueryBudgets

COMMUNITY_INSIGHTS_QUERY_POLICY_ID = "community-insights-query-policy"
COMMUNITY_INSIGHTS_QUERY_POLICY_VERSION = "1.0"

ALLOWED_STREAMS: frozenset[str] = frozenset(
    {
        "telemetry",
        "assessment_metadata",
        "cli_event",
        "extension_event",
        "ai_usage",
    }
)

SUPPORTED_SCHEMA_VERSIONS: frozenset[str] = frozenset({"1.0"})

MAX_DATE_SPAN_DAYS_DEFAULT = 31
MAX_DATE_SPAN_DAYS_LIFETIME = 365

METRIC_STREAMS: dict[str, tuple[str, ...]] = {
    "total_anonymous_installations": (
        "telemetry",
        "assessment_metadata",
        "cli_event",
        "extension_event",
        "ai_usage",
    ),
    "daily_active_installations": (
        "assessment_metadata",
        "telemetry",
        "cli_event",
        "extension_event",
        "ai_usage",
    ),
    "monthly_active_installations": (
        "assessment_metadata",
        "telemetry",
        "cli_event",
        "extension_event",
        "ai_usage",
    ),
    "first_assessments": ("assessment_metadata",),
    "repeat_assessments": ("assessment_metadata",),
    "successful_assessments": ("assessment_metadata",),
    "failed_assessments": ("assessment_metadata",),
    "cli_version_adoption": ("cli_event",),
    "assessment_head_usage": ("assessment_metadata",),
    "language_ecosystem_distribution": ("assessment_metadata",),
    "ai_provider_adoption": ("ai_usage",),
    "ai_model_adoption": ("ai_usage",),
    "vscode_extension_usage": ("extension_event",),
    "release_adoption": ("cli_event", "extension_event"),
}

LIFETIME_METRICS: frozenset[str] = frozenset(
    {
        "total_anonymous_installations",
        "first_assessments",
        "repeat_assessments",
    }
)

EXTERNAL_METRICS: frozenset[str] = frozenset({"validation_dataset_growth"})


def default_query_budgets() -> QueryBudgets:
    return QueryBudgets()
