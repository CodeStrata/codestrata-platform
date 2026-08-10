"""Contract for Slice 17.24 — Community Insights Production Auth."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SCHEMA_NAME = "community-insights-production-auth-verification"
SCHEMA_VERSION = "1.0.0"
PACKAGE_ID = "community-insights-production-auth-verification"
VERSION = "1.0.0"
SUITE_ID = "sv17-24"
SV1724_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv17-24"
REPORT_JSON = "community-insights-production-auth-verification.json"
REPORT_MD = "community-insights-production-auth-verification.md"

POLICY_RELATIVE = "platform/policies/community_insights_production_auth_policy.json"
POLICY_SCHEMA = "community-insights-production-auth-policy:1.0"
REGISTER_RELATIVE = "platform/policies/community_insights_production_auth_register.json"
REGISTER_SCHEMA = "community-insights-production-auth-register:1.0"
CONTRACT_RELATIVE = "platform/contracts/community_insights_production_auth_verification.json"
INSIGHTS_POLICY_RELATIVE = "insights/policies/community_insights_production_auth_policy.json"

INSIGHTS_AUTH_POLICY_RELATIVE = "platform/policies/community_insights_auth_policy.json"
INSIGHTS_AUTH_POLICY_INSIGHTS_RELATIVE = "insights/policies/community_insights_auth_policy.json"

LIVE_LOGIN_MATRIX_RELATIVE = (
    ".codestrata-artifacts/validation/suites/sv17-24/live-login-matrix.json"
)
ROTATION_DOC = "infrastructure/docs/runtime-security-secret-rotation.md"

ERRORS_PY = "platform/src/codestrata_platform/community_cloud_api/errors.py"
PASSWORD_PY = "platform/src/codestrata_platform/community_cloud_api/insights_auth/password.py"
SECRETS_PY = "platform/src/codestrata_platform/community_cloud_api/insights_auth/secrets.py"
AWS_SECRETS_PY = (
    "platform/src/codestrata_platform/community_cloud_api/insights_auth/aws_secrets.py"
)
INSIGHTS_AUTH_POLICY_PY = (
    "platform/src/codestrata_platform/community_cloud_api/insights_auth/policy.py"
)
INSIGHTS_AUTH_COOKIES_PY = (
    "platform/src/codestrata_platform/community_cloud_api/insights_auth/cookies.py"
)

INSIGHTS_AUTH_CONTEXT = "insights/src/auth/AuthContext.tsx"
INSIGHTS_AUTH_CLIENT = "insights/src/api/authClient.ts"

EXPECTED_17_23_PACKAGE = "verification/community_status_report_registry"
EXPECTED_17_24_PACKAGE = "verification/community_insights_production_auth"

SLICE_17_25_PACKAGE_CANDIDATES = (
    "verification/community_epic17_completion",
    "verification/community_docs_reconciliation",
    "verification/community_release_epic",
)

PASSWORD_SECRET_ID = "codestrata/insights/dashboard-password"
SESSION_SECRET_ID = "codestrata/insights/session-secret"

INSIGHTS_AUTH_PUBLIC_CODES = (
    "invalid_credentials",
    "session_expired",
    "invalid_session",
    "authorization_denied",
    "auth_service_unavailable",
    "invalid_origin",
    "rate_limited",
    "internal_auth_error",
)

POLICY_REQUIRED_VALUES: dict[str, object] = {
    "single_production_verifier_authority": True,
    "plaintext_not_stored_in_verifier_secret": True,
    "auth_fail_closed": True,
    "password_normalization_defined": True,
    "password_normalization_contract": "unicode_strip_edges_only",
    "session_cookie_secure": True,
    "cookie_path": "/",
    "cookie_http_only": True,
    "cookie_secure": True,
    "cookie_same_site": "Strict",
    "cookie_host_only": True,
    "rotation_behavior_defined": True,
    "password_verifier_not_cached": True,
    "session_secret_cache_ttl_seconds": 300,
    "production_login_e2e_required": True,
    "password_secret_id": PASSWORD_SECRET_ID,
    "session_secret_id": SESSION_SECRET_ID,
    "owner_once_bootstrap_allowed": True,
    "owner_password_manager_required": True,
    "marketplace_publish": False,
    "start_slice_17_24": True,
    "start_slice_17_25": False,
}

SOFT_LIMITATION_CODES = frozenset(
    {
        "worktree_uncommitted",
        "monorepo_pre_cutover_authority",
        "live_login_matrix_absent",
        "live_login_matrix_stale_deploy",
        "production_cookie_path_pending_deploy",
    }
)

HARD_FAIL_LIMITATION_CODES = frozenset(
    {
        "recurring_unexplained_invalid_password",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv1724Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    start_slice_17_24: bool = True
    start_slice_17_25: bool = False


def default_contract() -> Sv1724Contract:
    return Sv1724Contract()
