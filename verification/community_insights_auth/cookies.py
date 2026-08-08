"""Runtime cookie flag checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_auth._common import add_check, ensure_platform_importable
from verification.community_insights_auth.models import CheckResult, Defect


def check_cookies_runtime(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ensure_platform_importable(monorepo)

    from codestrata_platform.community_cloud_api.insights_auth.cookies import (
        build_set_cookie,
        cookie_flags_ok,
    )
    from codestrata_platform.community_cloud_api.insights_auth.policy import (
        default_insights_auth_policy,
    )

    policy = default_insights_auth_policy()
    cookie = build_set_cookie(policy=policy, token="redacted-token")
    add_check(
        checks,
        defects,
        "runtime:cookie_flags",
        cookie_flags_ok(cookie, require_secure=True),
        "httponly_secure_samesite",
        "runtime",
    )
    add_check(
        checks,
        defects,
        "runtime:cookie_host_only",
        "Domain=" not in cookie,
        "host_only",
        "runtime",
    )
    return checks, defects
