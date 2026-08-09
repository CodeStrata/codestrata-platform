"""Contract for Slice 15.5 community insights query strategy verification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.community_insights_query_strategy import (
    COMMUNITY_INSIGHTS_QUERY_STRATEGY_ID,
    COMMUNITY_INSIGHTS_QUERY_STRATEGY_VERSION,
)

SCHEMA_NAME = "community-insights-query-strategy-verification"
SCHEMA_VERSION = "1.0.0"
SV155_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv15-5"
REPORT_JSON = "community-insights-query-strategy-verification.json"
REPORT_MD = "community-insights-query-strategy-verification.md"

POLICY_ID = "community-insights-query-policy"
POLICY_VERSION = "1.0"
POLICY_RELATIVE = "platform/policies/community_insights_query_policy.json"
CONTRACT_RELATIVE = "platform/policies/community_insights_query_contract.json"
DOC_RELATIVE = "platform/docs/community-cloud-api/community-insights-query.md"
PLANNER_MODULE = (
    "platform/src/codestrata_platform/community_cloud_api/insights_query/planner.py"
)

LAKE_METRICS: tuple[str, ...] = (
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
)

FORBIDDEN_15_7_PATHS: tuple[str, ...] = (
    ".codestrata-artifacts/validation/suites/sv17-1",
)

ALLOWED_LIMITATIONS: frozenset[str] = frozenset(
    {
        "no_s3_reader_runtime_in_15_5",
        "no_aggregation_service_in_15_5",
        "no_dashboard_in_15_5",
        "reader_iam_unattached",
        "production_ingestion_still_unwired",
        "lifetime_checkpoint_deferred_to_15_7",
        "first_repeat_checkpoint_deferred_to_15_7",
        "worktree_uncommitted",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv155Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = COMMUNITY_INSIGHTS_QUERY_STRATEGY_ID
    package_version: str = COMMUNITY_INSIGHTS_QUERY_STRATEGY_VERSION
    start_slice_15_7: bool = False
    athena_required: bool = False
    no_aggregations: bool = True
    no_dashboard_ui: bool = True
    no_commit: bool = True


def default_contract() -> Sv155Contract:
    return Sv155Contract()
