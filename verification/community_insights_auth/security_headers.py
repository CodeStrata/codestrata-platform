"""Security headers and robots checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_auth._common import add_check
from verification.community_insights_auth.inventory import read_text
from verification.community_insights_auth.models import CheckResult, Defect


def check_security_headers(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    html = read_text(monorepo, "insights/index.html")

    add_check(
        checks,
        defects,
        "security:csp",
        "Content-Security-Policy" in html,
        "present",
        "frontend",
    )
    add_check(
        checks,
        defects,
        "security:x_content_type_options",
        "X-Content-Type-Options" in html,
        "present",
        "frontend",
    )
    add_check(
        checks,
        defects,
        "security:referrer_policy",
        "referrer" in html.lower(),
        "present",
        "frontend",
    )
    add_check(
        checks,
        defects,
        "security:permissions_policy",
        "Permissions-Policy" in html,
        "present",
        "frontend",
    )
    return checks, defects


def check_robots(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    html = read_text(monorepo, "insights/index.html")
    add_check(
        checks,
        defects,
        "robots:noindex",
        'name="robots" content="noindex,nofollow"' in html,
        "noindex",
        "frontend",
    )
    return checks, defects
