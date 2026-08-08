"""Epic 15 completion boundary checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_validation._common import add_check
from verification.community_insights_validation.contract import POLICY_RELATIVE
from verification.community_insights_validation.inventory import load_json
from verification.community_insights_validation.models import CheckResult, Defect


def check_epic_completion_boundary(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_json(monorepo, POLICY_RELATIVE)

    add_check(
        checks,
        defects,
        "epic:start_slice_16_3_false",
        policy.get("start_slice_16_3", False) is False,
        str(policy.get("start_slice_16_3", False)),
        "epic_completion_boundary",
    )
    add_check(
        checks,
        defects,
        "epic:15_12_completion_allowed",
        policy.get("start_slice_15_12") is True
        and policy.get("epic_15_12_deferred") is False,
        str(policy.get("start_slice_15_12")),
        "epic_completion_boundary",
    )
    add_check(
        checks,
        defects,
        "epic:validation_scope_present",
        bool(policy.get("validation_scope")),
        str(len(policy.get("validation_scope") or [])),
        "epic_completion_boundary",
    )
    return checks, defects
