"""Independent EIR aggregation/count checks for Slice 17.19."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_assessment_engineering_intelligence.contract import (
    EIR_JSON,
    INTELLIGENCE_RELATIVE,
    PORTFOLIO_ID,
)
from verification.community_assessment_engineering_intelligence.helpers import (
    check,
    hard_defect,
    load_json,
)
from verification.community_assessment_engineering_intelligence.models import (
    CheckResult,
    Defect,
)


def check_eir_aggregation(
    monorepo: Path,
    *,
    eir_generation: dict[str, Any] | None = None,
) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    gen = eir_generation or {}
    portfolio_id = str(gen.get("portfolio_id") or PORTFOLIO_ID)
    current = monorepo / INTELLIGENCE_RELATIVE / portfolio_id / "current"
    report_path = current / EIR_JSON
    coverage_path = current / "coverage.json"

    if not report_path.is_file():
        checks.append(
            check("eir_aggregation:report_present", False, "missing", "eir_aggregation")
        )
        defects.append(
            hard_defect(
                "missing_eir",
                "eir_aggregation:report_present",
                "present",
                "absent",
            )
        )
        return checks, defects, {"ok": False}

    report = load_json(report_path)
    ds = report.get("dataset_summary") if isinstance(report.get("dataset_summary"), dict) else {}
    claimed = int(ds.get("repository_count") or report.get("repository_count") or 0)

    included = 0
    if coverage_path.is_file():
        coverage = load_json(coverage_path)
        included = int(coverage.get("included_count") or 0)
        repos = coverage.get("repositories") or []
        if isinstance(repos, list) and included == 0:
            included = sum(1 for r in repos if isinstance(r, dict) and r.get("included"))
    else:
        # Fall back to membership / population fields.
        pop = report.get("repository_population")
        if isinstance(pop, list):
            included = len(pop)
        elif isinstance(pop, dict):
            included = int(pop.get("count") or pop.get("repository_count") or 0)
        drilldowns = report.get("repository_drilldowns") or []
        if isinstance(drilldowns, list) and included == 0:
            included = len(drilldowns)

    drilldowns = report.get("repository_drilldowns") or []
    drilldown_count = len(drilldowns) if isinstance(drilldowns, list) else int(
        ds.get("drilldown_count") or 0
    )

    count_ok = claimed >= 2 and (included == 0 or claimed == included or abs(claimed - included) == 0)
    # Prefer exact match when coverage exists.
    if coverage_path.is_file():
        count_ok = claimed == included and claimed >= 2

    checks.append(
        check(
            "eir_aggregation:repository_count",
            count_ok,
            f"claimed={claimed};included={included};drilldowns={drilldown_count}",
            "eir_aggregation",
        )
    )
    if not count_ok:
        defects.append(
            hard_defect(
                "aggregation_mismatch",
                "eir_aggregation:repository_count",
                str(included),
                str(claimed),
            )
        )

    summary = {
        "claimed_repository_count": claimed,
        "included_count": included,
        "drilldown_count": drilldown_count,
        "ok": count_ok,
    }
    return checks, defects, summary
