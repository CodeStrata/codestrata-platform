"""Aggregate checks for Slice 14.4."""

from __future__ import annotations

from pathlib import Path

from verification.engineering_intelligence_report_redesign.checks import (
    check_assessment_boundary,
    check_design_system,
    check_determinism,
    check_domain_boundary,
    check_negative_scenarios,
    check_policy,
    check_presentation_html,
    check_renderer,
)
from verification.engineering_intelligence_report_redesign.models import CheckResult, Defect


def release_posture() -> dict[str, bool]:
    return {
        "no_commit": True,
        "no_tag": True,
        "no_publish": True,
        "no_deploy": True,
        "start_slice_14_5": False,
        "assessment_html_unchanged_contract": True,
        "eir_domain_schema_unchanged": True,
        "slice_14_4_complete": True,
    }


def check_all(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    meta = {"design_system_consumed": False}

    c, d = check_policy(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, consumed = check_design_system(monorepo)
    checks.extend(c)
    defects.extend(d)
    meta["design_system_consumed"] = consumed

    c, d = check_domain_boundary(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, html = check_renderer(monorepo)
    checks.extend(c)
    defects.extend(d)

    checks.extend(check_presentation_html(html))

    c, d = check_assessment_boundary(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d = check_determinism(monorepo)
    checks.extend(c)
    defects.extend(d)

    checks.extend(check_negative_scenarios(monorepo, html))
    return checks, defects, meta
