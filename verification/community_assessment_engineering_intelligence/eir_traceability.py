"""EIR conclusion traceability for Slice 17.19."""

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


def check_eir_traceability(
    monorepo: Path,
    *,
    eir_generation: dict[str, Any] | None = None,
) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    gen = eir_generation or {}
    portfolio_id = str(gen.get("portfolio_id") or PORTFOLIO_ID)
    report_path = monorepo / INTELLIGENCE_RELATIVE / portfolio_id / "current" / EIR_JSON
    if not report_path.is_file():
        checks.append(
            check("eir_traceability:report_present", False, "missing", "eir_traceability")
        )
        defects.append(
            hard_defect(
                "missing_eir",
                "eir_traceability:report_present",
                "present",
                "absent",
            )
        )
        return checks, defects, {"ok": False}

    report = load_json(report_path)
    coverage_path = report_path.parent / "coverage.json"
    included = int(gen.get("included") or gen.get("repository_count") or 0)
    if coverage_path.is_file():
        coverage = load_json(coverage_path)
        included = int(coverage.get("included_count") or included)

    patterns = report.get("recurring_patterns") or report.get("patterns") or []
    observations = (
        report.get("modernization_observations")
        or report.get("observations")
        or []
    )
    multi_ok = True
    weak = 0
    for collection_name, collection in (
        ("patterns", patterns),
        ("observations", observations),
    ):
        if not isinstance(collection, list):
            continue
        for item in collection:
            if not isinstance(item, dict):
                continue
            repos = item.get("repository_ids") or item.get("repositories") or []
            # Claims that look multi-repo must cite >=2 repositories.
            title = str(item.get("title") or item.get("summary") or "").lower()
            claims_multi = any(
                word in title for word in ("across", "portfolio", "multiple", "recurring")
            ) or int(item.get("repository_count") or 0) >= 2
            if claims_multi and isinstance(repos, list) and len(repos) < 2:
                multi_ok = False
                weak += 1
            _ = collection_name

    checks.append(
        check(
            "eir_traceability:multi_repo_patterns",
            multi_ok,
            f"weak={weak}",
            "eir_traceability",
        )
    )
    if not multi_ok:
        defects.append(
            hard_defect(
                "untraceable_pattern",
                "eir_traceability:multi_repo_patterns",
                "repository_ids>=2",
                f"weak={weak}",
            )
        )

    drilldowns = report.get("repository_drilldowns") or []
    drill_len = len(drilldowns) if isinstance(drilldowns, list) else 0
    # Drilldowns should match included count when both known.
    drill_ok = included == 0 or drill_len == 0 or drill_len == included
    checks.append(
        check(
            "eir_traceability:drilldowns_match_included",
            drill_ok,
            f"drilldowns={drill_len};included={included}",
            "eir_traceability",
        )
    )
    if not drill_ok:
        defects.append(
            hard_defect(
                "drilldown_mismatch",
                "eir_traceability:drilldowns_match_included",
                str(included),
                str(drill_len),
            )
        )

    summary = {
        "included": included,
        "drilldown_count": drill_len,
        "weak_multi_repo_claims": weak,
        "ok": multi_ok and drill_ok,
    }
    return checks, defects, summary
