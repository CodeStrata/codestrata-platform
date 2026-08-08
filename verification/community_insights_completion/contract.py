"""Contract for Slice 15.12 Epic 15 completion verification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.community_insights_completion import (
    COMMUNITY_INSIGHTS_COMPLETION_ID,
    COMMUNITY_INSIGHTS_COMPLETION_VERSION,
)

SCHEMA_NAME = "community-insights-completion-verification"
SCHEMA_VERSION = "1.0.0"
SV1512_OUTPUT_RELATIVE = "reports/verification/sv15-12"
REPORT_JSON = "community-insights-completion-verification.json"
REPORT_MD = "community-insights-completion-verification.md"

POLICY_ID = "community-insights-completion-policy"
POLICY_VERSION = "1.0"
POLICY_RELATIVE = "platform/policies/community_insights_completion_policy.json"

EPIC = "15"
EPIC_TITLE = "Community Insights"
TOTAL_SLICES = 12
DESIGN_SYSTEM_AUTHORITY = "design-system/"
INSIGHTS_APP_ROOT = "insights"

# slice, module, schema, title, policy_id
PRIOR_SLICE_RUNNERS: tuple[tuple[str, str, str, str, str], ...] = (
    (
        "15.1",
        "verification.community_data_lake_audit.runner",
        "community-data-lake-audit-verification",
        "Audit Community Data Lake Implementation",
        "community-data-lake-policy:1.0",
    ),
    (
        "15.2",
        "verification.community_analytics_partition.runner",
        "community-analytics-partition-verification",
        "Validate & Standardize Analytics Partition Strategy",
        "community-analytics-partition-policy:1.0",
    ),
    (
        "15.3",
        "verification.community_insights_event_coverage.runner",
        "community-insights-event-coverage-verification",
        "Validate Event Schemas & Dashboard Metric Coverage",
        "community-insights-event-coverage-policy:1.0",
    ),
    (
        "15.4",
        "verification.community_insights_ingestion.runner",
        "community-insights-ingestion-verification",
        "Harden Privacy-Safe Analytics Ingestion",
        "community-insights-ingestion-policy:1.0",
    ),
    (
        "15.5",
        "verification.community_insights_query_strategy.runner",
        "community-insights-query-strategy-verification",
        "Validate Bounded S3 Query Strategy",
        "community-insights-query-policy:1.0",
    ),
    (
        "15.6",
        "verification.community_insights_metrics.runner",
        "community-insights-metrics-verification",
        "Define Community Insights Metrics & Privacy Contract",
        "community-insights-metrics-policy:1.0",
    ),
    (
        "15.7",
        "verification.community_insights_aggregation.runner",
        "community-insights-aggregation-verification",
        "Build Privacy-Safe On-Demand Aggregation Service",
        "community-insights-aggregation-policy:1.0",
    ),
    (
        "15.8",
        "verification.community_insights_application.runner",
        "community-insights-application-verification",
        "Build insights.codestrata.ai Application",
        "codestrata-insights-application-policy:1.0",
    ),
    (
        "15.9",
        "verification.community_insights_auth.runner",
        "community-insights-auth-verification",
        "Dashboard Authentication & Access Control",
        "community-insights-auth-policy:1.0",
    ),
    (
        "15.10",
        "verification.community_insights_dashboard.runner",
        "community-insights-dashboard-verification",
        "Dashboard Metrics & Visualizations",
        "codestrata-insights-dashboard-policy:1.0",
    ),
    (
        "15.11",
        "verification.community_insights_validation.runner",
        "community-insights-validation-verification",
        "Dashboard Validation",
        "community-insights-validation-policy:1.0",
    ),
)

EPIC15_POLICIES: tuple[tuple[str, str, str], ...] = (
    (
        "community-data-lake-policy",
        "1.0",
        "platform/policies/community_data_lake_policy.json",
    ),
    (
        "community-analytics-partition-policy",
        "1.0",
        "platform/policies/community_analytics_partition_policy.json",
    ),
    (
        "community-insights-event-coverage-policy",
        "1.0",
        "platform/policies/community_insights_event_coverage_policy.json",
    ),
    (
        "community-insights-ingestion-policy",
        "1.0",
        "platform/policies/community_insights_ingestion_policy.json",
    ),
    (
        "community-insights-query-policy",
        "1.0",
        "platform/policies/community_insights_query_policy.json",
    ),
    (
        "community-insights-metrics-policy",
        "1.0",
        "platform/policies/community_insights_metrics_policy.json",
    ),
    (
        "community-insights-aggregation-policy",
        "1.0",
        "platform/policies/community_insights_aggregation_policy.json",
    ),
    (
        "codestrata-insights-application-policy",
        "1.0",
        "platform/policies/codestrata_insights_application_policy.json",
    ),
    (
        "community-insights-auth-policy",
        "1.0",
        "platform/policies/community_insights_auth_policy.json",
    ),
    (
        "codestrata-insights-dashboard-policy",
        "1.0",
        "platform/policies/codestrata_insights_dashboard_policy.json",
    ),
    (
        "community-insights-validation-policy",
        "1.0",
        "platform/policies/community_insights_validation_policy.json",
    ),
    (
        "community-insights-completion-policy",
        "1.0",
        POLICY_RELATIVE,
    ),
)

FORBIDDEN_EPIC16_PATHS: tuple[str, ...] = (
    "reports/verification/sv17-1",
)

FORBIDDEN_EPIC16_PACKAGES: tuple[str, ...] = (
    "verification/repository_cleanup",
)

ALLOWED_LIMITATIONS: frozenset[str] = frozenset(
    {
        "no_live_production_analytics",
        "production_ingestion_disabled",
        "no_real_secrets_manager_integration",
        "no_deployed_insights_site",
        "retention_only_first_repeat_history",
        "optional_installation_id_undercount",
        "validation_dataset_current_size_only",
        "no_formal_wcag_certification",
        "one_browser_os",
        "worktree_uncommitted",
        "future_private_remote_not_created",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv1512Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = COMMUNITY_INSIGHTS_COMPLETION_ID
    package_version: str = COMMUNITY_INSIGHTS_COMPLETION_VERSION
    start_epic_16: bool = True
    start_slice_16_2: bool = True
    start_slice_16_3: bool = True
    start_slice_16_4: bool = True
    start_slice_16_5: bool = True
    start_slice_16_6: bool = True
    start_slice_16_7: bool = True
    start_slice_16_8: bool = True
    start_slice_16_9: bool = True
    start_slice_16_10: bool = True
    start_epic_17: bool = False
    no_commit: bool = True
    no_tag: bool = True
    no_publish: bool = True
    no_deploy: bool = True
    production_ingestion_enabled: bool = False
    live_dashboard_data_available: bool = False
    insights_site_deployed: bool = False
    real_secrets_created: bool = False
    remote_insights_repository_created: bool = False


def default_contract() -> Sv1512Contract:
    return Sv1512Contract()
