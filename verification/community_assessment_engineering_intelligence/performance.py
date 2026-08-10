"""Performance / size class observations for Slice 17.19."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_assessment_engineering_intelligence.contract import (
    ASSESSMENT_HTML,
    ASSESSMENT_JSON,
    EIR_HTML,
    EIR_JSON,
    INTELLIGENCE_RELATIVE,
    PORTFOLIO_ID,
)
from verification.community_assessment_engineering_intelligence.helpers import check
from verification.community_assessment_engineering_intelligence.models import (
    CheckResult,
    Defect,
)


def _size_class(nbytes: int) -> str:
    if nbytes < 50_000:
        return "small"
    if nbytes < 500_000:
        return "medium"
    if nbytes < 5_000_000:
        return "large"
    return "xlarge"


def check_performance(
    monorepo: Path,
    selection: dict[str, Any],
    *,
    eir_generation: dict[str, Any] | None = None,
) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    sizes: dict[str, Any] = {}

    for item in selection.get("selected") or []:
        catalog_id = str(item.get("catalog_id") or "")
        rel = item.get("current_relative")
        if not rel:
            continue
        current = monorepo / str(rel)
        entry: dict[str, Any] = {}
        for name in (ASSESSMENT_JSON, ASSESSMENT_HTML):
            path = current / name
            if path.is_file():
                nbytes = path.stat().st_size
                entry[name] = {"bytes": nbytes, "class": _size_class(nbytes)}
        heads = current / "heads"
        if heads.is_dir():
            total = sum(p.stat().st_size for p in heads.glob("*.json"))
            entry["heads_total"] = {"bytes": total, "class": _size_class(total)}
        sizes[catalog_id] = entry

    gen = eir_generation or {}
    portfolio_id = str(gen.get("portfolio_id") or PORTFOLIO_ID)
    eir_current = monorepo / INTELLIGENCE_RELATIVE / portfolio_id / "current"
    eir_sizes: dict[str, Any] = {}
    for name in (EIR_JSON, EIR_HTML):
        path = eir_current / name
        if path.is_file():
            nbytes = path.stat().st_size
            eir_sizes[name] = {"bytes": nbytes, "class": _size_class(nbytes)}

    classification = "ACCEPTABLE_V0_2_0"
    checks.append(
        check(
            "performance:classification",
            classification == "ACCEPTABLE_V0_2_0",
            classification,
            "performance",
        )
    )
    summary = {
        "assessments": sizes,
        "eir": eir_sizes,
        "classification": classification,
    }
    return checks, defects, summary
