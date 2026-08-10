"""Portfolio Engineering Intelligence checks against on-disk artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from verification.community_22_repository_validation.contract import (
    INTELLIGENCE_RELATIVE,
    PORTFOLIO_EIR_COUNT,
)
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


def check_engineering_intelligence(
    *,
    monorepo: Path,
    portfolio_enabled: bool,
    portfolio_eir_count: int,
    skip_execute: bool,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    add_check(
        checks,
        defects,
        "engineering_intelligence:enabled",
        portfolio_enabled is True,
        "true",
        "engineering_intelligence",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    add_check(
        checks,
        defects,
        "engineering_intelligence:eir_count_policy",
        portfolio_eir_count == PORTFOLIO_EIR_COUNT,
        str(portfolio_eir_count),
        "engineering_intelligence",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    add_check(
        checks,
        defects,
        "engineering_intelligence:output_root",
        INTELLIGENCE_RELATIVE.startswith(".codestrata-artifacts/"),
        INTELLIGENCE_RELATIVE,
        "engineering_intelligence",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    if skip_execute:
        add_check(
            checks,
            defects,
            "engineering_intelligence:build_status",
            True,
            "not_executed",
            "engineering_intelligence",
            CheckResult=CheckResult,
            Defect=Defect,
        )
        return checks, defects

    portfolios = _portfolio_dirs(monorepo)
    add_check(
        checks,
        defects,
        "engineering_intelligence:single_portfolio",
        len(portfolios) == PORTFOLIO_EIR_COUNT,
        f"count={len(portfolios)}",
        "engineering_intelligence",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    if not portfolios:
        return checks, defects

    portfolio = portfolios[0]
    report_json = portfolio / "engineering-intelligence-report.json"
    report_html = portfolio / "engineering-intelligence-report.html"
    coverage = portfolio / "coverage.json"
    add_check(
        checks,
        defects,
        "engineering_intelligence:artifacts",
        report_json.is_file() and report_html.is_file(),
        "json+html",
        "engineering_intelligence",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    coverage_payload: dict[str, Any] = {}
    if coverage.is_file():
        try:
            coverage_payload = json.loads(coverage.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            coverage_payload = {}
    included = int(coverage_payload.get("included_count") or coverage_payload.get("included") or 0)
    excluded = coverage_payload.get("excluded") or coverage_payload.get("excluded_assessments") or []
    add_check(
        checks,
        defects,
        "engineering_intelligence:coverage_recorded",
        coverage.is_file(),
        f"included={included};excluded={len(excluded) if isinstance(excluded, list) else excluded}",
        "engineering_intelligence",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    # No absolute paths / secrets in EIR JSON.
    if report_json.is_file():
        blob = report_json.read_text(encoding="utf-8")
        add_check(
            checks,
            defects,
            "engineering_intelligence:no_absolute_paths",
            "/Users/" not in blob and "s3://" not in blob.lower(),
            "sanitized",
            "engineering_intelligence",
            CheckResult=CheckResult,
            Defect=Defect,
        )
    return checks, defects
