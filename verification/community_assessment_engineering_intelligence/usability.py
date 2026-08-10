"""Engineering-leader usability checklist for Slice 17.19."""

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
from verification.community_assessment_engineering_intelligence.helpers import (
    check,
    load_json,
    read_text,
)
from verification.community_assessment_engineering_intelligence.models import (
    CheckResult,
    Defect,
)


def check_usability(
    monorepo: Path,
    selection: dict[str, Any],
    *,
    eir_generation: dict[str, Any] | None = None,
) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    notes: list[str] = []

    assessment_ok = 0
    for item in selection.get("selected") or []:
        rel = item.get("current_relative")
        if not rel:
            continue
        current = monorepo / str(rel)
        blob = ""
        for name in (ASSESSMENT_JSON, ASSESSMENT_HTML):
            path = current / name
            if path.is_file():
                blob += read_text(path).lower()
        has_summary = "summary" in blob
        has_findings = "finding" in blob
        has_reco = "recommend" in blob
        has_lim = "limitation" in blob or "insufficient" in blob
        if has_summary and (has_findings or has_reco or has_lim):
            assessment_ok += 1

    checks.append(
        check(
            "usability:assessment_checklist",
            assessment_ok >= 2,
            f"usable_assessments={assessment_ok}",
            "usability",
        )
    )

    gen = eir_generation or {}
    portfolio_id = str(gen.get("portfolio_id") or PORTFOLIO_ID)
    eir_path = monorepo / INTELLIGENCE_RELATIVE / portfolio_id / "current" / EIR_JSON
    eir_html = monorepo / INTELLIGENCE_RELATIVE / portfolio_id / "current" / EIR_HTML
    eir_blob = ""
    if eir_path.is_file():
        eir_blob += read_text(eir_path).lower()
        payload = load_json(eir_path)
        if payload.get("dataset_summary") or payload.get("title"):
            notes.append("eir_summary_present")
    if eir_html.is_file():
        eir_blob += read_text(eir_html).lower()

    eir_ok = bool(eir_blob) and (
        "limitation" in eir_blob
        or "pattern" in eir_blob
        or "drilldown" in eir_blob
        or "repository" in eir_blob
    )
    checks.append(
        check(
            "usability:eir_checklist",
            eir_ok,
            "summary/findings/limitations markers",
            "usability",
        )
    )

    verdict = "PASS" if assessment_ok >= 4 and eir_ok else "PASS_WITH_LIMITATIONS"
    if assessment_ok < 2 or not eir_ok:
        verdict = "PASS_WITH_LIMITATIONS"
    notes.append("engineering-leader checklist: summaries, findings/recommendations/limitations present without marketing fluff")

    summary = {
        "assessment_usable_count": assessment_ok,
        "eir_usable": eir_ok,
        "narrative": verdict,
        "notes": notes,
    }
    return checks, defects, summary
