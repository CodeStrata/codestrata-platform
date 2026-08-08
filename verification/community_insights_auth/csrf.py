"""CSRF posture checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_auth._common import add_check, ensure_platform_importable
from verification.community_insights_auth.contract import AUTH_PACKAGE
from verification.community_insights_auth.inventory import read_text
from verification.community_insights_auth.models import CheckResult, Defect


def check_csrf(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    csrf_py = read_text(monorepo, f"{AUTH_PACKAGE}/csrf.py")
    service_py = read_text(monorepo, f"{AUTH_PACKAGE}/service.py")

    add_check(
        checks,
        defects,
        "csrf:origin_allowed_helper",
        "origin_allowed" in csrf_py,
        "present",
        "cors_csrf",
    )
    add_check(
        checks,
        defects,
        "csrf:service_checks_origin",
        "check_origin" in service_py and "origin_allowed" in service_py,
        "wired",
        "cors_csrf",
    )

    ensure_platform_importable(monorepo)
    from codestrata_platform.community_cloud_api.insights_auth.csrf import origin_allowed
    from codestrata_platform.community_cloud_api.insights_auth.policy import (
        default_insights_auth_policy,
    )

    policy = default_insights_auth_policy()
    add_check(
        checks,
        defects,
        "csrf:production_origin",
        origin_allowed(
            origin=policy.future_frontend_origin,
            referer=None,
            policy=policy,
        ),
        "allowed",
        "cors_csrf",
    )
    add_check(
        checks,
        defects,
        "csrf:foreign_origin_rejected",
        not origin_allowed(origin="https://evil.example", referer=None, policy=policy),
        "rejected",
        "cors_csrf",
    )
    return checks, defects
