"""Contract for Slice 15.1 Community Data Lake audit verification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.community_data_lake_audit import (
    COMMUNITY_DATA_LAKE_AUDIT_ID,
    COMMUNITY_DATA_LAKE_AUDIT_VERSION,
)

SCHEMA_NAME = "community-data-lake-audit-verification"
SCHEMA_VERSION = "1.0.0"
SV151_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv15-1"
REPORT_JSON = "community-data-lake-audit-verification.json"
REPORT_MD = "community-data-lake-audit-verification.md"

POLICY_ID = "community-data-lake-policy"
POLICY_VERSION = "1.0"
POLICY_RELATIVE = "platform/policies/community_data_lake_policy.json"
CONTRACT_DOC_RELATIVE = (
    "platform/docs/community-cloud-api/community-data-lake-contract.md"
)
PYTHON_POLICY_MODULE = (
    "platform/src/codestrata_platform/community_cloud_api/data_lake/policy.py"
)

ACCEPTED_STREAMS: tuple[str, ...] = (
    "telemetry",
    "assessment_metadata",
    "cli_event",
    "extension_event",
    "ai_usage",
)

FINDING_CLASSES: tuple[str, ...] = (
    "Accepted",
    "Requires Change",
    "Historical",
    "Deferred",
)

FORBIDDEN_15_7_PATHS: tuple[str, ...] = (
    ".codestrata-artifacts/validation/suites/sv17-1",
)

ALLOWED_LIMITATIONS: frozenset[str] = frozenset(
    {
        "production_ingestion_deliberately_unwired",
        "writer_iam_unattached",
        "retention_defaults_require_release_owner_review",
        "no_athena_glue_query_layer",
        "no_community_insights_dashboard",
        "no_aggregations_in_15_1",
        "worktree_uncommitted",
        "stale_docs_require_change_tracked",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv151Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = COMMUNITY_DATA_LAKE_AUDIT_ID
    package_version: str = COMMUNITY_DATA_LAKE_AUDIT_VERSION
    start_slice_15_7: bool = False
    no_telemetry_redesign: bool = True
    no_schema_redesign: bool = True
    no_aggregations: bool = True
    no_dashboard: bool = True
    no_commit: bool = True
    no_tag: bool = True
    no_publish: bool = True
    no_deploy: bool = True


def default_contract() -> Sv151Contract:
    return Sv151Contract()
