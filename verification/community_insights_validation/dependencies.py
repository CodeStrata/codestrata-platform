"""Dependency boundary checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_validation._common import add_check
from verification.community_insights_validation.contract import FORBIDDEN_CHART_PACKAGES, PACKAGE_JSON
from verification.community_insights_validation.inventory import load_json
from verification.community_insights_validation.models import CheckResult, Defect


def check_dependencies(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    pkg = load_json(monorepo, PACKAGE_JSON)
    deps = {**(pkg.get("dependencies") or {}), **(pkg.get("devDependencies") or {})}

    for forbidden in FORBIDDEN_CHART_PACKAGES:
        add_check(
            checks,
            defects,
            f"dependencies:no_{forbidden.replace('.', '_')}",
            forbidden not in deps,
            "absent",
            "security",
        )
    add_check(
        checks,
        defects,
        "dependencies:package_name",
        pkg.get("name") == "codestrata-insights",
        str(pkg.get("name")),
        "security",
    )
    return checks, defects
