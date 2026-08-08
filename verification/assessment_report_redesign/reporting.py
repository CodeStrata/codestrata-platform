"""Aggregate checks and report assembly helpers."""

from __future__ import annotations

from pathlib import Path

from verification.assessment_report_redesign.design_system import check_design_system
from verification.assessment_report_redesign.determinism import check_determinism
from verification.assessment_report_redesign.eir_boundary import check_eir_boundary
from verification.assessment_report_redesign.models import CheckResult, Defect
from verification.assessment_report_redesign.policy import check_policy
from verification.assessment_report_redesign.renderer import check_renderer
from verification.assessment_report_redesign.scenarios import check_negative_scenarios
from verification.assessment_report_redesign.schema_boundary import check_schema_boundary
from verification.assessment_report_redesign.shell import (
    check_accessibility,
    check_assessment_heads,
    check_evidence,
    check_executive_summary,
    check_findings,
    check_navigation,
    check_offline,
    check_print,
    check_recommendations,
    check_responsive,
    check_scores,
    check_shell,
    check_statuses,
)


def release_posture() -> dict[str, bool]:
    return {
        "no_commit": True,
        "no_tag": True,
        "no_publish": True,
        "no_deploy": True,
        "start_slice_14_4": False,
        "assessment_schema_unchanged": True,
        "eir_unchanged": True,
        "slice_14_3_complete": True,
    }


def check_all(
    monorepo: Path,
    tmp_path: Path,
) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    meta = {
        "design_system_consumed": False,
    }

    c, d = check_policy(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, consumed = check_design_system(monorepo)
    checks.extend(c)
    defects.extend(d)
    meta["design_system_consumed"] = consumed

    c, d = check_schema_boundary(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, html = check_renderer(monorepo, tmp_path)
    checks.extend(c)
    defects.extend(d)

    for fn in (
        check_shell,
        check_executive_summary,
        check_assessment_heads,
        check_findings,
        check_evidence,
        check_recommendations,
        check_scores,
        check_statuses,
        check_navigation,
        check_responsive,
        check_print,
        check_accessibility,
        check_offline,
    ):
        checks.extend(fn(html))

    c, d = check_determinism(tmp_path / "det")
    checks.extend(c)
    defects.extend(d)

    c, d = check_eir_boundary(monorepo)
    checks.extend(c)
    defects.extend(d)

    checks.extend(check_negative_scenarios(monorepo, html))
    return checks, defects, meta
