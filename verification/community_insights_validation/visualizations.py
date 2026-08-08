"""Visualization boundary checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_validation._common import add_check, frontend_source_blob
from verification.community_insights_validation.contract import FORBIDDEN_CHART_PACKAGES
from verification.community_insights_validation.inventory import load_json, read_text
from verification.community_insights_validation.models import CheckResult, Defect


def check_visualizations(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    source = frontend_source_blob(monorepo)
    distribution = read_text(
        monorepo, "insights/src/components/charts/DistributionChart.tsx"
    )
    dashboard = read_text(monorepo, "insights/src/pages/DashboardPage.tsx")

    add_check(
        checks,
        defects,
        "visualizations:local_css_svg",
        "HorizontalBarChart" in distribution,
        "present",
        "ui",
    )
    add_check(
        checks,
        defects,
        "visualizations:no_line_chart",
        "LineChart" not in source and "timeSeries" not in source.lower(),
        "absent",
        "ui",
    )
    add_check(
        checks,
        defects,
        "visualizations:no_growth_chart",
        "Growth chart" not in dashboard
        and "Historical growth tracking is not available yet" in dashboard,
        "size_not_growth",
        "ui",
    )

    pkg = load_json(monorepo, "insights/package.json")
    deps = {**(pkg.get("dependencies") or {}), **(pkg.get("devDependencies") or {})}
    found = [name for name in FORBIDDEN_CHART_PACKAGES if name in deps]
    add_check(
        checks,
        defects,
        "visualizations:no_forbidden_packages",
        not found,
        "absent" if not found else ",".join(found),
        "ui",
    )
    return checks, defects
