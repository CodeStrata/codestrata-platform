"""Contract for Slice 15.7 aggregation verification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.community_insights_aggregation import (
    COMMUNITY_INSIGHTS_AGGREGATION_ID,
    COMMUNITY_INSIGHTS_AGGREGATION_VERSION,
)

SCHEMA_NAME = "community-insights-aggregation-verification"
SCHEMA_VERSION = "1.0.0"
SV157_OUTPUT_RELATIVE = "reports/verification/sv15-7"
REPORT_JSON = "community-insights-aggregation-verification.json"
REPORT_MD = "community-insights-aggregation-verification.md"

POLICY_ID = "community-insights-aggregation-policy"
POLICY_VERSION = "1.0"
POLICY_RELATIVE = "platform/policies/community_insights_aggregation_policy.json"
CONTRACT_RELATIVE = "platform/policies/community_insights_aggregation_contract.json"
DOC_RELATIVE = "platform/docs/community-cloud-api/community-insights-aggregation.md"

INSIGHTS_PACKAGE = (
    "platform/src/codestrata_platform/community_cloud_api/insights"
)
STORAGE_PACKAGE = (
    "platform/src/codestrata_platform/community_cloud_api/insights_storage"
)

FORBIDDEN_15_8_PATHS: tuple[str, ...] = (
    "reports/verification/sv17-1",
)

ALLOWED_LIMITATIONS: frozenset[str] = frozenset(
    {
        "production_ingestion_still_unwired",
        "no_live_dashboard_data_claim",
        "first_repeat_retention_only",
        "validation_growth_snapshots_unavailable",
        "cache_mode_none",
        "no_derived_checkpoint_artifact",
        "reader_iam_unattached",
        "worktree_uncommitted",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv157Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = COMMUNITY_INSIGHTS_AGGREGATION_ID
    package_version: str = COMMUNITY_INSIGHTS_AGGREGATION_VERSION
    start_slice_15_8: bool = False
    athena_required: bool = False
    no_dashboard_ui: bool = True
    no_auth: bool = True
    no_commit: bool = True


def default_contract() -> Sv157Contract:
    return Sv157Contract()
