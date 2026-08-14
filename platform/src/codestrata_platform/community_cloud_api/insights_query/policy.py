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

SUPPORTED_SCHEMA_VERSIONS: frozenset[str] = frozenset({"1.0", "1.1"})

MAX_DATE_SPAN_DAYS_DEFAULT = 31
MAX_DATE_SPAN_DAYS_LIFETIME = 365

# Epic 20 / Slice 20.7 — explicit metric authorities (no double-count):
# - Total / Successful / Failed Assessments = lifecycle telemetry only
# - First / Repeat = telemetry + assessment_metadata with pairing so old
#   telemetry-only clients keep working while new dual-emit clients count once
# - Published Reports = external publish registry (not listed here)
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
    "first_assessments": ("telemetry", "assessment_metadata"),
    "repeat_assessments": ("telemetry", "assessment_metadata"),
    "successful_assessments": ("telemetry",),
    "failed_assessments": ("telemetry",),
    "total_assessments": ("telemetry",),
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

EXTERNAL_METRICS: frozenset[str] = frozenset(
    {
        "validation_dataset_growth",
        "github_stars",
        "github_forks",
        "published_reports",
        "community_sentiment",
    }
)


def default_query_budgets() -> QueryBudgets:
    return QueryBudgets()
