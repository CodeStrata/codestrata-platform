"""Portfolio membership change under stable portfolio_id for Slice 17.19."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_assessment_engineering_intelligence.contract import (
    EIR_JSON,
    INTELLIGENCE_RELATIVE,
    PORTFOLIO_ID,
)
from verification.community_assessment_engineering_intelligence.eir_generation import (
    generate_eir_for_selection,
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


def check_membership(
    monorepo: Path,
    selection: dict[str, Any],
    *,
    eir_generation: dict[str, Any] | None = None,
) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {"portfolio_id": PORTFOLIO_ID}

    # Portfolio A should already exist from eir_generation (6 repos).
    gen_a = eir_generation or {}
    count_a = int(gen_a.get("repository_count") or gen_a.get("included") or 0)

    # Portfolio B = drop express, same portfolio_id.
    ids_b = [
        str(s["catalog_id"])
        for s in (selection.get("selected") or [])
        if s.get("catalog_id") != "express" and s.get("current_relative")
    ]
    try:
        gen_b = generate_eir_for_selection(
            monorepo,
            selection,
            catalog_ids=ids_b,
            portfolio_id=PORTFOLIO_ID,
        )
    except Exception as exc:  # noqa: BLE001
        checks.append(
            check("membership:portfolio_b", False, type(exc).__name__, "membership")
        )
        defects.append(
            hard_defect(
                "membership_b_failed",
                "membership:portfolio_b",
                "generated",
                type(exc).__name__,
            )
        )
        return checks, defects, summary

    count_b = int(gen_b.get("repository_count") or gen_b.get("included") or 0)
    current = monorepo / INTELLIGENCE_RELATIVE / PORTFOLIO_ID / "current"
    previous = monorepo / INTELLIGENCE_RELATIVE / PORTFOLIO_ID / "previous"
    previous_ok = previous.is_dir() and (previous / EIR_JSON).is_file()
    current_ok = current.is_dir() and (current / EIR_JSON).is_file()

    differ = count_a != count_b and count_b == len(ids_b)
    checks.append(
        check(
            "membership:counts_differ",
            differ or (count_b == 5 and count_a >= 5),
            f"a={count_a};b={count_b}",
            "membership",
        )
    )
    checks.append(
        check(
            "membership:previous_inspectable",
            previous_ok,
            "previous/engineering-intelligence-report.json",
            "membership",
        )
    )
    checks.append(
        check(
            "membership:same_portfolio_id",
            current_ok and PORTFOLIO_ID in str(current),
            PORTFOLIO_ID,
            "membership",
        )
    )

    if previous_ok:
        prev = load_json(previous / EIR_JSON)
        prev_count = int(
            ((prev.get("dataset_summary") or {}) if isinstance(prev.get("dataset_summary"), dict) else {}).get(
                "repository_count"
            )
            or prev.get("repository_count")
            or 0
        )
        summary["previous_repository_count"] = prev_count

    if not previous_ok:
        defects.append(
            hard_defect(
                "membership_previous",
                "membership:previous_inspectable",
                "present",
                "absent",
            )
        )

    summary.update(
        {
            "portfolio_a_count": count_a,
            "portfolio_b_count": count_b,
            "dropped": "express",
            "previous_present": previous_ok,
            "current_present": current_ok,
        }
    )
    return checks, defects, summary
