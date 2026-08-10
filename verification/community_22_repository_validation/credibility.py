"""Credibility checks including head-coverage limitations."""

from __future__ import annotations

from verification.community_22_repository_validation.helpers import add_check
from verification.community_22_repository_validation.models import CheckResult, Defect


def check_credibility(
    *,
    skip_execute: bool,
    suite_execution_status: str,
    repository_results: list[dict[str, object]],
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    invented_pass = skip_execute and any(
        r.get("assessment_status") == "pass" for r in repository_results
    )
    add_check(
        checks,
        defects,
        "credibility:no_invented_pass",
        not invented_pass,
        "no fabricated PASS before execution"
        if not invented_pass
        else "fabricated PASS while skip_execute",
        "credibility",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    add_check(
        checks,
        defects,
        "credibility:scaffolding_status_honest",
        suite_execution_status in {"not_executed", "scaffolding", "partial", "complete"},
        suite_execution_status,
        "credibility",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    if skip_execute:
        add_check(
            checks,
            defects,
            "credibility:skip_execute_not_complete",
            suite_execution_status != "complete",
            suite_execution_status,
            "credibility",
            CheckResult=CheckResult,
            Defect=Defect,
        )
        return checks, defects

    executed = [
        r
        for r in repository_results
        if r.get("assessment_status") not in {None, "not_executed", "not_attempted"}
    ]
    add_check(
        checks,
        defects,
        "credibility:executed_results_present",
        len(executed) == 22,
        f"executed={len(executed)}",
        "credibility",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    passed = [
        r
        for r in executed
        if r.get("assessment_status") in {"pass", "present", "pass_with_limitations"}
    ]
    add_check(
        checks,
        defects,
        "credibility:all_assessable_passed",
        len(passed) == len(executed),
        f"passed={len(passed)}/{len(executed)}",
        "credibility",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    # Limited head coverage must remain explicit (not silently upgraded).
    doris = next(
        (r for r in repository_results if r.get("repository_validation_id") == "doris"),
        None,
    )
    if doris is not None:
        heads = str(doris.get("head_status_summary") or "")
        limited = heads.startswith("heads=2") or doris.get("quality_class") == "PASS_WITH_LIMITATIONS"
        add_check(
            checks,
            defects,
            "credibility:doris_limitation_explicit",
            limited or heads.startswith("heads="),
            heads or "missing",
            "credibility",
            CheckResult=CheckResult,
            Defect=Defect,
        )
    return checks, defects
