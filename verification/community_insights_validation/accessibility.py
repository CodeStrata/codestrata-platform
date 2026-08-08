"""Accessibility checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_validation._common import add_check
from verification.community_insights_validation.inventory import exists, read_text
from verification.community_insights_validation.models import CheckResult, Defect


def check_accessibility(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    login = read_text(monorepo, "insights/src/pages/LoginPage.tsx")
    dashboard = read_text(monorepo, "insights/src/pages/DashboardPage.tsx")

    add_check(
        checks,
        defects,
        "accessibility:a11y_module",
        exists(monorepo, "insights/src/accessibility/a11y.ts"),
        "present",
        "accessibility",
    )
    add_check(
        checks,
        defects,
        "accessibility:login_labels",
        "htmlFor" in login and "aria-invalid" in login,
        "labeled",
        "accessibility",
    )
    add_check(
        checks,
        defects,
        "accessibility:dashboard_sections",
        'id="activity"' in dashboard or 'id=\"activity\"' in dashboard,
        "landmarks",
        "accessibility",
    )
    return checks, defects
