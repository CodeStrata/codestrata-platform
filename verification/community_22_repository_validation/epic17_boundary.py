"""Epic 17 boundary checks for Slice 17.13."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_22_repository_validation.contract import POLICY_RELATIVE
from verification.community_22_repository_validation.helpers import add_check, read_json
from verification.community_22_repository_validation.models import CheckResult, Defect


def check_epic17_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {
        "start_slice_17_12": True,
        "start_slice_17_13": True,
        "start_slice_17_14": False,
    }

    policy_path = monorepo / POLICY_RELATIVE
    policy: dict[str, Any] = {}
    if policy_path.is_file():
        policy = read_json(policy_path)
        summary["start_slice_17_13"] = policy.get("start_slice_17_13", False)
        summary["start_slice_17_14"] = policy.get("start_slice_17_14", False)

    add_check(
        checks,
        defects,
        "boundary:17_13_true",
        summary["start_slice_17_13"] is True,
        "true",
        "epic17_boundary",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    add_check(
        checks,
        defects,
        "boundary:17_14_false",
        summary["start_slice_17_14"] is False,
        "false",
        "epic17_boundary",
        CheckResult=CheckResult,
        Defect=Defect,
    )

    slice_14_candidates = [
        "platform/policies/community_cloud_slice_17_14_policy.json",
        "platform/policies/community_production_slice_17_14_policy.json",
        "platform/policies/community_22_repository_validation_slice_17_14_policy.json",
    ]
    for candidate in slice_14_candidates:
        absent = not (monorepo / candidate).is_file()
        add_check(
            checks,
            defects,
            f"boundary:slice_17_14_absent:{Path(candidate).stem}",
            absent,
            "absent",
            "epic17_boundary",
            CheckResult=CheckResult,
            Defect=Defect,
        )

    release = policy.get("release_boundary") or {}
    add_check(
        checks,
        defects,
        "boundary:release_no_commit",
        release.get("commit_required") is False,
        "false",
        "epic17_boundary",
        CheckResult=CheckResult,
        Defect=Defect,
    )

    return checks, defects, summary
