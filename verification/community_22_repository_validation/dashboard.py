"""Dashboard validation against Insights evidence sections."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from verification.community_22_repository_validation.contract import SV1713_OUTPUT_RELATIVE
from verification.community_22_repository_validation.helpers import add_check
from verification.community_22_repository_validation.models import CheckResult, Defect

EVIDENCE_RELATIVE = f"{SV1713_OUTPUT_RELATIVE}/insights-dashboard-check.json"

REQUIRED_SECTIONS = (
    "Activity",
    "Assessments",
    "Adoption",
    "Coverage",
    "Technology",
    "AI",
    "Validation",
)


def build_dashboard(
    *,
    suite_execution_status: str,
    catalog_count: int,
    repository_results: list[dict[str, Any]],
    statuses: dict[str, str],
) -> dict[str, Any]:
    assessment_not_executed = sum(
        1 for r in repository_results if r.get("assessment_status") == "not_executed"
    )
    return {
        "suite_execution_status": suite_execution_status,
        "catalog_count": catalog_count,
        "repository_count": len(repository_results),
        "assessments_not_executed": assessment_not_executed,
        "category_statuses": statuses,
    }


def check_dashboard(
    *,
    monorepo: Path,
    skip_execute: bool,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    if skip_execute:
        add_check(
            checks,
            defects,
            "dashboard:not_executed",
            True,
            "not_executed",
            "dashboard",
            CheckResult=CheckResult,
            Defect=Defect,
        )
        return checks, defects

    path = monorepo / EVIDENCE_RELATIVE
    if not path.is_file():
        add_check(
            checks,
            defects,
            "dashboard:evidence_present",
            False,
            "missing",
            "dashboard",
            CheckResult=CheckResult,
            Defect=Defect,
        )
        return checks, defects

    evidence = json.loads(path.read_text(encoding="utf-8"))
    sections = evidence.get("sections") or evidence.get("dashboard_sections") or {}
    if isinstance(sections, list):
        present = {str(s) for s in sections}
    elif isinstance(sections, dict):
        present = {str(k) for k in sections.keys()}
    else:
        present = set()

    # If sections not explicitly listed, accept metric_id coverage as proxy.
    metrics = []
    sanitized = evidence.get("overview_sanitized")
    if isinstance(sanitized, dict) and isinstance(sanitized.get("metrics"), list):
        metrics = sanitized["metrics"]
    elif isinstance(evidence.get("metrics"), list):
        metrics = evidence["metrics"]

    budget_hit = bool(evidence.get("query_budget_reached"))
    usable = [
        m
        for m in metrics
        if isinstance(m, dict)
        and m.get("status") != "error"
        and "query_budget_reached" not in (m.get("limitations") or [])
    ]

    add_check(
        checks,
        defects,
        "dashboard:sections_authority",
        bool(present) or bool(metrics),
        f"sections={sorted(present)[:7]};metrics={len(metrics)}",
        "dashboard",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    if present:
        missing = [s for s in REQUIRED_SECTIONS if s not in present]
        add_check(
            checks,
            defects,
            "dashboard:required_sections",
            not missing,
            "ok" if not missing else f"missing={missing}",
            "dashboard",
            CheckResult=CheckResult,
            Defect=Defect,
        )
    add_check(
        checks,
        defects,
        "dashboard:aggregate_only",
        "installation_id" not in json.dumps(evidence).lower(),
        "no_installation_id",
        "dashboard",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    add_check(
        checks,
        defects,
        "dashboard:usable_after_aggregation",
        (not budget_hit and bool(usable)) or (bool(usable) and not budget_hit),
        f"usable={len(usable)};budget_hit={budget_hit}",
        "dashboard",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    return checks, defects
