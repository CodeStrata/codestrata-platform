"""Contract for Slice 15.3 community insights event coverage."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.community_insights_event_coverage import (
    COMMUNITY_INSIGHTS_EVENT_COVERAGE_ID,
    COMMUNITY_INSIGHTS_EVENT_COVERAGE_VERSION,
)

SCHEMA_NAME = "community-insights-event-coverage-verification"
SCHEMA_VERSION = "1.0.0"
SV153_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv15-3"
REPORT_JSON = "community-insights-event-coverage-verification.json"
REPORT_MD = "community-insights-event-coverage-verification.md"

POLICY_ID = "community-insights-event-coverage-policy"
POLICY_VERSION = "1.0"
POLICY_RELATIVE = "platform/policies/community_insights_event_coverage_policy.json"
CONTRACT_DOC_RELATIVE = (
    "platform/docs/community-cloud-api/community-insights-event-coverage.md"
)
BASELINE_LAKE_POLICY = "platform/policies/community_data_lake_policy.json"
BASELINE_PARTITION_POLICY = (
    "platform/policies/community_analytics_partition_policy.json"
)

DASHBOARD_METRICS: tuple[str, ...] = (
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

STREAMS: tuple[str, ...] = (
    "telemetry",
    "assessment_metadata",
    "cli_event",
    "extension_event",
    "ai_usage",
)

FORBIDDEN_15_7_PATHS: tuple[str, ...] = (
    ".codestrata-artifacts/validation/suites/sv17-1",
)

ALLOWED_LIMITATIONS: frozenset[str] = frozenset(
    {
        "production_ingestion_still_unwired",
        "installation_id_optional_may_undercount",
        "vscode_epic10_identity_free",
        "package_ecosystem_optional",
        "model_adoption_family_granularity_only",
        "no_aggregations_built_in_15_3",
        "no_schema_activation_in_15_3",
        "worktree_uncommitted",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv153Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = COMMUNITY_INSIGHTS_EVENT_COVERAGE_ID
    package_version: str = COMMUNITY_INSIGHTS_EVENT_COVERAGE_VERSION
    start_slice_15_7: bool = False
    no_path_redesign: bool = True
    no_schema_activation: bool = True
    no_ingestion_enablement: bool = True
    no_aggregations: bool = True
    no_dashboard_ui: bool = True
    no_commit: bool = True


def default_contract() -> Sv153Contract:
    return Sv153Contract()
