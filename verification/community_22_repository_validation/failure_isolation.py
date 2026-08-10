"""Failure isolation helpers."""

from __future__ import annotations

from verification.community_22_repository_validation.helpers import add_check
from verification.community_22_repository_validation.models import CheckResult, Defect


def check_failure_isolation(repository_results: list[dict[str, object]]) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ids = [str(r.get("repository_validation_id")) for r in repository_results]
    add_check(
        checks,
        defects,
        "failure_isolation:unique_repository_ids",
        len(ids) == len(set(ids)),
        str(len(ids)),
        "failure_isolation",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    return checks, defects
