"""Policy checks for Slice 15.9 auth verification."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_auth._common import add_check
from verification.community_insights_auth.contract import (
    PASSWORD_SECRET_ID,
    POLICY_ID,
    POLICY_RELATIVE,
    POLICY_VERSION,
    SESSION_SECRET_ID,
)
from verification.community_insights_auth.inventory import load_json
from verification.community_insights_auth.models import CheckResult, Defect


def check_policy(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_json(monorepo, POLICY_RELATIVE)

    add_check(checks, defects, "policy:present", bool(policy), "present", "policy")
    add_check(
        checks,
        defects,
        "policy:id",
        policy.get("policy_id") == POLICY_ID,
        "configured",
        "policy",
    )
    add_check(
        checks,
        defects,
        "policy:version",
        policy.get("policy_version") == POLICY_VERSION,
        "configured",
        "policy",
    )
    add_check(
        checks,
        defects,
        "policy:shared_password_auth",
        policy.get("shared_password_auth") is True,
        "enabled",
        "policy",
    )
    add_check(
        checks,
        defects,
        "policy:individual_accounts_false",
        policy.get("individual_accounts") is False,
        "disabled",
        "policy",
    )
    add_check(
        checks,
        defects,
        "policy:secrets_manager_authority",
        policy.get("secrets_manager_authority") is True,
        "enabled",
        "policy",
    )
    add_check(
        checks,
        defects,
        "policy:frontend_secret_storage_false",
        policy.get("frontend_secret_storage") is False,
        "disabled",
        "policy",
    )
    add_check(
        checks,
        defects,
        "policy:session_ttl",
        policy.get("session_ttl_seconds") == 28800,
        "28800",
        "policy",
    )
    add_check(
        checks,
        defects,
        "policy:http_only_cookie",
        policy.get("http_only_cookie") is True,
        "enabled",
        "policy",
    )
    add_check(
        checks,
        defects,
        "policy:secure_cookie",
        policy.get("secure_cookie") is True,
        "enabled",
        "policy",
    )
    add_check(
        checks,
        defects,
        "policy:same_site_strict",
        policy.get("same_site_policy") == "Strict",
        "Strict",
        "policy",
    )
    add_check(
        checks,
        defects,
        "policy:production_deployment_enabled_false",
        policy.get("production_deployment_enabled") is False,
        "disabled",
        "policy",
    )
    add_check(
        checks,
        defects,
        "policy:start_slice_16_3_false",
        policy.get("start_slice_16_3", False) is False,
        "false",
        "policy",
    )
    add_check(
        checks,
        defects,
        "policy:password_secret_id",
        policy.get("password_secret_id") == PASSWORD_SECRET_ID,
        "configured",
        "policy",
    )
    add_check(
        checks,
        defects,
        "policy:session_secret_id",
        policy.get("session_secret_id") == SESSION_SECRET_ID,
        "configured",
        "policy",
    )
    add_check(
        checks,
        defects,
        "policy:no_cognito_oauth",
        policy.get("cognito") is False
        and policy.get("oauth") is False
        and policy.get("social_login") is False,
        "disabled",
        "policy",
    )
    add_check(
        checks,
        defects,
        "policy:session_signing_separate",
        policy.get("session_signing_reuses_dashboard_password") is False,
        "separate",
        "policy",
    )
    return checks, defects
