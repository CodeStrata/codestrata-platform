"""Insights auth policy constants and loader."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

COMMUNITY_INSIGHTS_AUTH_POLICY_ID = "community-insights-auth-policy"
COMMUNITY_INSIGHTS_AUTH_POLICY_VERSION = "1.0"
COMMUNITY_INSIGHTS_AUTH_POLICY_URN = (
    f"{COMMUNITY_INSIGHTS_AUTH_POLICY_ID}:{COMMUNITY_INSIGHTS_AUTH_POLICY_VERSION}"
)

DEFAULT_PASSWORD_SECRET_ID = "codestrata/insights/dashboard-password"
DEFAULT_SESSION_SECRET_ID = "codestrata/insights/session-secret"
DEFAULT_COOKIE_NAME = "cs_insights_session"
DEFAULT_COOKIE_PATH = "/"
DEFAULT_SESSION_TTL_SECONDS = 28800
DEFAULT_SAME_SITE = "Strict"
DEFAULT_FRONTEND_ORIGIN = "https://insights.codestrata.ai"
ROLE_AUTHENTICATED_INTERNAL = "authenticated_internal"

SESSION_VERSION = 1


@dataclass(frozen=True, slots=True)
class InsightsAuthPolicy:
    policy_id: str = COMMUNITY_INSIGHTS_AUTH_POLICY_ID
    policy_version: str = COMMUNITY_INSIGHTS_AUTH_POLICY_VERSION
    shared_password_auth: bool = True
    individual_accounts: bool = False
    secrets_manager_authority: bool = True
    frontend_secret_storage: bool = False
    server_side_verification: bool = True
    session_required: bool = True
    http_only_cookie: bool = True
    secure_cookie: bool = True
    same_site_policy: str = DEFAULT_SAME_SITE
    session_ttl_seconds: int = DEFAULT_SESSION_TTL_SECONDS
    logout_supported: bool = True
    authentication_required_for_metrics: bool = True
    raw_event_access_allowed: bool = False
    auth_failure_logging_safe: bool = True
    production_deployment_enabled: bool = False
    password_secret_id: str = DEFAULT_PASSWORD_SECRET_ID
    session_secret_id: str = DEFAULT_SESSION_SECRET_ID
    cookie_name: str = DEFAULT_COOKIE_NAME
    cookie_path: str = DEFAULT_COOKIE_PATH
    cookie_host_only: bool = True
    future_frontend_origin: str = DEFAULT_FRONTEND_ORIGIN
    cors_wildcard_with_credentials: bool = False
    password_verifier: str = "scrypt"
    session_signing_reuses_dashboard_password: bool = False
    start_slice_15_10: bool = False

    @property
    def urn(self) -> str:
        return f"{self.policy_id}:{self.policy_version}"


def default_insights_auth_policy() -> InsightsAuthPolicy:
    return InsightsAuthPolicy()


def load_insights_auth_policy(path: Path | None = None) -> InsightsAuthPolicy:
    """Load policy JSON when present; otherwise return defaults."""

    if path is None:
        # platform/src/codestrata_platform/community_cloud_api/insights_auth/policy.py
        # → parents[5] = platform/
        candidate = (
            Path(__file__).resolve().parents[4] / "policies" / "community_insights_auth_policy.json"
        )
        # parents: insights_auth, community_cloud_api, codestrata_platform, src, platform
        path = candidate
        if not path.is_file():
            # monorepo: platform/policies from repo root via parents[5]
            alt = (
                Path(__file__).resolve().parents[5]
                / "platform"
                / "policies"
                / "community_insights_auth_policy.json"
            )
            path = alt if alt.is_file() else candidate

    if not path.is_file():
        return default_insights_auth_policy()

    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return InsightsAuthPolicy(
        policy_id=str(data.get("policy_id", COMMUNITY_INSIGHTS_AUTH_POLICY_ID)),
        policy_version=str(data.get("policy_version", COMMUNITY_INSIGHTS_AUTH_POLICY_VERSION)),
        shared_password_auth=bool(data.get("shared_password_auth", True)),
        individual_accounts=bool(data.get("individual_accounts", False)),
        secrets_manager_authority=bool(data.get("secrets_manager_authority", True)),
        frontend_secret_storage=bool(data.get("frontend_secret_storage", False)),
        server_side_verification=bool(data.get("server_side_verification", True)),
        session_required=bool(data.get("session_required", True)),
        http_only_cookie=bool(data.get("http_only_cookie", True)),
        secure_cookie=bool(data.get("secure_cookie", True)),
        same_site_policy=str(data.get("same_site_policy", DEFAULT_SAME_SITE)),
        session_ttl_seconds=int(data.get("session_ttl_seconds", DEFAULT_SESSION_TTL_SECONDS)),
        logout_supported=bool(data.get("logout_supported", True)),
        authentication_required_for_metrics=bool(
            data.get("authentication_required_for_metrics", True)
        ),
        raw_event_access_allowed=bool(data.get("raw_event_access_allowed", False)),
        auth_failure_logging_safe=bool(data.get("auth_failure_logging_safe", True)),
        production_deployment_enabled=bool(data.get("production_deployment_enabled", False)),
        password_secret_id=str(data.get("password_secret_id", DEFAULT_PASSWORD_SECRET_ID)),
        session_secret_id=str(data.get("session_secret_id", DEFAULT_SESSION_SECRET_ID)),
        cookie_name=str(data.get("cookie_name", DEFAULT_COOKIE_NAME)),
        cookie_path=str(data.get("cookie_path", DEFAULT_COOKIE_PATH)),
        cookie_host_only=bool(data.get("cookie_host_only", True)),
        future_frontend_origin=str(
            data.get("future_frontend_origin", DEFAULT_FRONTEND_ORIGIN)
        ),
        cors_wildcard_with_credentials=bool(
            data.get("cors_wildcard_with_credentials", False)
        ),
        password_verifier=str(data.get("password_verifier", "scrypt")),
        session_signing_reuses_dashboard_password=bool(
            data.get("session_signing_reuses_dashboard_password", False)
        ),
        start_slice_15_10=bool(data.get("start_slice_15_10", False)),
    )
