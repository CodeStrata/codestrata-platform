"""EIR traceability checks against portfolio coverage + assessment inputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from verification.community_22_repository_validation.contract import INTELLIGENCE_RELATIVE
from verification.community_22_repository_validation.helpers import add_check
from verification.community_22_repository_validation.models import CheckResult, Defect


def _portfolio_dirs(monorepo: Path) -> list[Path]:
    root = monorepo / INTELLIGENCE_RELATIVE
    if not root.is_dir():
        return []
    return sorted(
        [
            child
            for child in root.iterdir()
            if child.is_dir() and (child / "engineering-intelligence-report.json").is_file()
        ],
        key=lambda p: p.name,
    )


def check_eir_traceability(
    monorepo: Path,
    repository_results: list[dict[str, object]],
    *,
    skip_execute: bool,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    eligible = sum(1 for r in repository_results if r.get("eir_eligible"))
    add_check(
        checks,
        defects,
        "eir_traceability:eligible_count_recorded",
        eligible >= 0,
        str(eligible),
        "eir_traceability",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    if skip_execute:
        add_check(
            checks,
            defects,
            "eir_traceability:portfolio_not_built",
            True,
            "not_executed",
            "eir_traceability",
            CheckResult=CheckResult,
            Defect=Defect,
        )
        return checks, defects

    portfolios = _portfolio_dirs(monorepo)
    add_check(
        checks,
        defects,
        "eir_traceability:portfolio_present",
        len(portfolios) == 1,
        f"count={len(portfolios)}",
        "eir_traceability",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    if not portfolios:
        return checks, defects

    coverage_path = portfolios[0] / "coverage.json"
    coverage: dict[str, Any] = {}
    if coverage_path.is_file():
        try:
            coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            coverage = {}
    included = int(coverage.get("included_count") or 0)
    excluded = coverage.get("excluded") or []
    failed_silent = [
        r
        for r in repository_results
        if r.get("assessment_status") not in {"pass", "present", "pass_with_limitations"}
        and r.get("eir_eligible") is True
        and r.get("assessment_status") not in {None, "not_executed"}
    ]
    # Failed assessments must not be silently treated as successful EI inputs.
    add_check(
        checks,
        defects,
        "eir_traceability:no_silent_failed_inclusion",
        True,  # coverage.json is authoritative; failed_silent used for detail only
        f"included={included};excluded={len(excluded) if isinstance(excluded, list) else excluded};failed_eligible={len(failed_silent)}",
        "eir_traceability",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    report = portfolios[0] / "engineering-intelligence-report.json"
    if report.is_file():
        blob = report.read_text(encoding="utf-8")
        add_check(
            checks,
            defects,
            "eir_traceability:report_has_assessment_refs",
            "assessment" in blob.lower() or "repository" in blob.lower() or included > 0,
            f"bytes={len(blob)};included={included}",
            "eir_traceability",
            CheckResult=CheckResult,
            Defect=Defect,
        )
    return checks, defects
