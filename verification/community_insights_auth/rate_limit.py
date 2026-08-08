"""Rate limit posture checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_auth._common import add_check
from verification.community_insights_auth.contract import AUTH_PACKAGE
from verification.community_insights_auth.inventory import load_json, read_text
from verification.community_insights_auth.models import CheckResult, Defect


def check_rate_limit(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_json(monorepo, "platform/policies/community_insights_auth_policy.json")
    routes = read_text(monorepo, f"{AUTH_PACKAGE}/routes.py")

    add_check(
        checks,
        defects,
        "rate_limit:policy_posture",
        "auth_attempt" in str(policy.get("rate_limit_posture", "")),
        "configured",
        "platform",
    )
    add_check(
        checks,
        defects,
        "rate_limit:login_group",
        'rate_limit_group="auth_attempt"' in routes,
        "auth_attempt",
        "platform",
    )
    return checks, defects
