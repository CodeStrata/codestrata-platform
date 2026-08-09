"""Contract for Slice 15.2 community analytics partition verification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.community_analytics_partition import (
    COMMUNITY_ANALYTICS_PARTITION_ID,
    COMMUNITY_ANALYTICS_PARTITION_VERSION,
)

SCHEMA_NAME = "community-analytics-partition-verification"
SCHEMA_VERSION = "1.0.0"
SV152_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv15-2"
REPORT_JSON = "community-analytics-partition-verification.json"
REPORT_MD = "community-analytics-partition-verification.md"

POLICY_ID = "community-analytics-partition-policy"
POLICY_VERSION = "1.0"
POLICY_RELATIVE = "platform/policies/community_analytics_partition_policy.json"
CONTRACT_DOC_RELATIVE = (
    "platform/docs/community-cloud-api/community-analytics-partition.md"
)
BASELINE_POLICY_RELATIVE = "platform/policies/community_data_lake_policy.json"

SUPPORT_CLASSES: tuple[str, ...] = (
    "Supported directly",
    "Requires bounded aggregation",
    "Requires future enhancement",
    "Not applicable",
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

FORBIDDEN_15_7_PATHS: tuple[str, ...] = (
    ".codestrata-artifacts/validation/suites/sv17-1",
)

ALLOWED_LIMITATIONS: frozenset[str] = frozenset(
    {
        "production_ingestion_still_unwired",
        "no_aggregations_built_in_15_2",
        "no_athena_glue_catalog_in_15_2",
        "installation_id_optional_may_undercount",
        "named_ecosystems_not_in_payload",
        "worktree_uncommitted",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv152Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = COMMUNITY_ANALYTICS_PARTITION_ID
    package_version: str = COMMUNITY_ANALYTICS_PARTITION_VERSION
    start_slice_15_7: bool = False
    no_partition_redesign: bool = True
    no_aggregations: bool = True
    no_dashboard_ui: bool = True
    no_ingestion_enablement: bool = True
    no_commit: bool = True


def default_contract() -> Sv152Contract:
    return Sv152Contract()
