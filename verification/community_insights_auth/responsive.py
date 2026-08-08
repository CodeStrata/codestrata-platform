"""Responsive layout checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_auth._common import add_check
from verification.community_insights_auth.inventory import read_text
from verification.community_insights_auth.models import CheckResult, Defect


def check_responsive(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    html = read_text(monorepo, "insights/index.html")
    css = read_text(monorepo, "insights/src/designSystem/app.css")

    add_check(
        checks,
        defects,
        "responsive:viewport_meta",
        'name="viewport"' in html,
        "present",
        "frontend",
    )
    add_check(
        checks,
        defects,
        "responsive:login_styles",
        "cs-login" in css,
        "present",
        "frontend",
    )
    return checks, defects
