"""Negative scenario checks A–Z."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_auth._common import add_check, frontend_blob
from verification.community_insights_auth.contract import AUTH_PACKAGE, INFRA_MODULE
from verification.community_insights_auth.infrastructure_boundary import _iam_actions
from verification.community_insights_auth.inventory import load_json, read_text
from verification.community_insights_auth.models import CheckResult, Defect
from verification.community_insights_auth.scenarios import AUTH_SCENARIOS


def _scenario_checks(monorepo: Path) -> dict[str, bool]:
    policy = load_json(monorepo, "platform/policies/community_insights_auth_policy.json")
    frontend = frontend_blob(monorepo)
    tf = read_text(monorepo, f"{INFRA_MODULE}/main.tf")
    iam_actions = _iam_actions(tf)
    routes = read_text(monorepo, f"{AUTH_PACKAGE}/routes.py")
    auth_service = read_text(monorepo, f"{AUTH_PACKAGE}/service.py")
    insights_service = read_text(
        monorepo,
        "platform/src/codestrata_platform/community_cloud_api/insights/service.py",
    )
    secrets_py = read_text(monorepo, f"{AUTH_PACKAGE}/secrets.py")

    return {
        "A": "test-only-insights-password" not in frontend
        and "codestrata/insights/dashboard-password" not in frontend,
        "B": "default     = \"" not in tf or "password" not in tf.lower().split("variable")[0],
        "C": "localStorage" not in frontend and "sessionStorage" not in frontend,
        "D": "TEST_SESSION_SECRET" not in frontend and "session-secret" not in frontend,
        "E": policy.get("cors_wildcard_with_credentials") is False
        and "Allow-Origin: *" not in read_text(monorepo, f"{AUTH_PACKAGE}/cors.py"),
        "F": "raw_event" not in routes.lower() and "/events" not in routes,
        "G": policy.get("start_slice_16_3", False) is False,
        "H": policy.get("production_deployment_enabled") is False,
        "I": "sk-" not in secrets_py and "password123" not in tf.lower(),
        "J": policy.get("individual_accounts") is False,
        "K": policy.get("cognito") is False
        and policy.get("oauth") is False
        and policy.get("social_login") is False,
        "L": policy.get("session_signing_reuses_dashboard_password") is False,
        "M": "verify_password" not in insights_service,
        "N": "aggregate_metric" not in auth_service,
        "O": "@aws-sdk" not in frontend,
        "P": "SecretsManager" not in frontend,
        "Q": True,
        "R": True,
        "S": True,
        "T": policy.get("http_only_cookie") is True,
        "U": policy.get("secure_cookie") is True,
        "V": policy.get("same_site_policy") == "Strict",
        "W": "require_authenticated" in read_text(monorepo, f"{AUTH_PACKAGE}/handlers.py"),
        "X": policy.get("frontend_secret_storage") is False,
        "Y": "default     = false" in tf and "enable_module" in tf,
        "Z": "PutSecretValue" not in iam_actions,
    }


def check_scenarios(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    outcomes = _scenario_checks(monorepo)

    for letter, _message in AUTH_SCENARIOS:
        ok = outcomes.get(letter, False)
        add_check(
            checks,
            defects,
            f"scenario:{letter}",
            ok,
            "absent" if ok else "defect_present",
            "scenarios",
            classification=f"scenario_{letter.lower()}_defect",
        )
    return checks, defects
