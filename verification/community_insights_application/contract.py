"""Contract for Slice 15.8 Insights application verification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.community_insights_application import (
    COMMUNITY_INSIGHTS_APPLICATION_ID,
    COMMUNITY_INSIGHTS_APPLICATION_VERSION,
)

SCHEMA_NAME = "community-insights-application-verification"
SCHEMA_VERSION = "1.0.0"
SV158_OUTPUT_RELATIVE = "reports/verification/sv15-8"
REPORT_JSON = "community-insights-application-verification.json"
REPORT_MD = "community-insights-application-verification.md"

POLICY_ID = "codestrata-insights-application-policy"
POLICY_VERSION = "1.0"
POLICY_RELATIVE = "platform/policies/codestrata_insights_application_policy.json"
REPO_CONTRACT_RELATIVE = "platform/policies/codestrata_insights_repository_contract.json"
APP_ROOT = "insights"
PACKAGE_JSON = "insights/package.json"

FORBIDDEN_15_9_PATHS: tuple[str, ...] = (
    "reports/verification/sv17-1",
)

ALLOWED_LIMITATIONS: frozenset[str] = frozenset(
    {
        "production_deploy_disabled",
        "production_ingestion_still_unwired",
        "no_live_dashboard_data_claim",
        "worktree_uncommitted",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv158Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = COMMUNITY_INSIGHTS_APPLICATION_ID
    package_version: str = COMMUNITY_INSIGHTS_APPLICATION_VERSION
    start_slice_15_9: bool = False
    no_auth: bool = True
    no_deploy: bool = True
    no_commit: bool = True


def default_contract() -> Sv158Contract:
    return Sv158Contract()
