"""Contract for Slice 15.6 community insights metrics verification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.community_insights_metrics import (
    COMMUNITY_INSIGHTS_METRICS_ID,
    COMMUNITY_INSIGHTS_METRICS_VERSION,
)

SCHEMA_NAME = "community-insights-metrics-verification"
SCHEMA_VERSION = "1.0.0"
SV156_OUTPUT_RELATIVE = "reports/verification/sv15-6"
REPORT_JSON = "community-insights-metrics-verification.json"
REPORT_MD = "community-insights-metrics-verification.md"

POLICY_ID = "community-insights-metrics-policy"
POLICY_VERSION = "1.0"
POLICY_RELATIVE = "platform/policies/community_insights_metrics_policy.json"
CONTRACT_RELATIVE = "platform/policies/community_insights_metrics_contract.json"
DOC_RELATIVE = "platform/docs/community-cloud-api/community-insights-metrics.md"

METRIC_IDS: tuple[str, ...] = (
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

REQUIRED_METRIC_FIELDS: tuple[str, ...] = (
    "metric_id",
    "display_name",
    "description",
    "source_streams",
    "required_fields",
    "time_window",
    "deduplication_rule",
    "grouping_dimensions",
    "numerator",
    "denominator",
    "completeness_semantics",
    "privacy_classification",
    "known_limitations",
    "external_internal_source",
    "aggregation_strategy_hint",
    "allowed_dashboard_representation",
    "forbidden_interpretation",
)

FORBIDDEN_15_7_PATHS: tuple[str, ...] = (
    "reports/verification/sv17-1",
)

ALLOWED_LIMITATIONS: frozenset[str] = frozenset(
    {
        "production_ingestion_still_unwired",
        "no_live_dashboard_data_claim",
        "optional_installation_id_undercount",
        "first_repeat_checkpoint_deferred_to_15_7",
        "validation_growth_snapshots_not_yet_defined",
        "no_aggregation_runtime_in_15_6",
        "no_dashboard_in_15_6",
        "worktree_uncommitted",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv156Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = COMMUNITY_INSIGHTS_METRICS_ID
    package_version: str = COMMUNITY_INSIGHTS_METRICS_VERSION
    start_slice_15_7: bool = False
    no_aggregations: bool = True
    no_dashboard_ui: bool = True
    no_auth: bool = True
    no_commit: bool = True


def default_contract() -> Sv156Contract:
    return Sv156Contract()
