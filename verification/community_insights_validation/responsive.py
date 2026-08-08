"""Responsive layout checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_validation._common import add_check
from verification.community_insights_validation.inventory import read_text
from verification.community_insights_validation.models import CheckResult, Defect


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
        "responsive",
    )
    add_check(
        checks,
        defects,
        "responsive:app_styles",
        "cs-page" in css or "cs-login" in css,
        "present",
        "responsive",
    )
    return checks, defects
