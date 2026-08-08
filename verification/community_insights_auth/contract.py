"""Contract for Slice 15.9 auth verification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.community_insights_auth import (
    COMMUNITY_INSIGHTS_AUTH_VERIFICATION_ID,
    COMMUNITY_INSIGHTS_AUTH_VERIFICATION_VERSION,
)

SCHEMA_NAME = "community-insights-auth-verification"
SCHEMA_VERSION = "1.0.0"
SV159_OUTPUT_RELATIVE = "reports/verification/sv15-9"
REPORT_JSON = "community-insights-auth-verification.json"
REPORT_MD = "community-insights-auth-verification.md"

POLICY_ID = "community-insights-auth-policy"
POLICY_VERSION = "1.0"
POLICY_RELATIVE = "platform/policies/community_insights_auth_policy.json"
AUTH_CONTRACT_RELATIVE = "platform/policies/community_insights_auth_contract.json"

AUTH_PACKAGE = "platform/src/codestrata_platform/community_cloud_api/insights_auth"
INFRA_MODULE = "infrastructure/modules/community-insights-auth"

AUTH_PACKAGE_FILES: tuple[str, ...] = (
    f"{AUTH_PACKAGE}/password.py",
    f"{AUTH_PACKAGE}/session.py",
    f"{AUTH_PACKAGE}/cookies.py",
    f"{AUTH_PACKAGE}/service.py",
    f"{AUTH_PACKAGE}/routes.py",
    f"{AUTH_PACKAGE}/secrets.py",
    f"{AUTH_PACKAGE}/handlers.py",
    f"{AUTH_PACKAGE}/cors.py",
    f"{AUTH_PACKAGE}/csrf.py",
    f"{AUTH_PACKAGE}/policy.py",
    f"{AUTH_PACKAGE}/errors.py",
)

FRONTEND_AUTH_FILES: tuple[str, ...] = (
    "insights/src/pages/LoginPage.tsx",
    "insights/src/api/authClient.ts",
    "insights/src/auth/AuthContext.tsx",
    "insights/src/app/App.tsx",
    "insights/index.html",
)

PASSWORD_SECRET_ID = "codestrata/insights/dashboard-password"
SESSION_SECRET_ID = "codestrata/insights/session-secret"

FORBIDDEN_15_10_PATHS: tuple[str, ...] = (
    "reports/verification/sv17-1",
)

ALLOWED_LIMITATIONS: frozenset[str] = frozenset(
    {
        "production_deployment_disabled",
        "no_real_secrets",
        "production_ingestion_still_unwired",
        "worktree_uncommitted",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv159Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = COMMUNITY_INSIGHTS_AUTH_VERIFICATION_ID
    package_version: str = COMMUNITY_INSIGHTS_AUTH_VERIFICATION_VERSION
    start_slice_15_10: bool = True
    start_slice_15_11: bool = False
    production_deployment_enabled: bool = False
    no_aws: bool = True
    no_deploy: bool = True
    no_commit: bool = True


def default_contract() -> Sv159Contract:
    return Sv159Contract()
