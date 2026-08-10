"""Prior slice (17.12) dependency checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_22_repository_validation.contract import (
    ARTIFACT_ROOT,
    ASSESSMENTS_RELATIVE,
    VALIDATION_RELATIVE,
)
from verification.community_22_repository_validation.helpers import add_check
from verification.community_22_repository_validation.models import CheckResult, Defect


def check_prior_slices(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    consolidation_policy = monorepo / "platform/policies/community_artifact_consolidation_policy.json"
    add_check(
        checks,
        defects,
        "prior:17_12_policy_exists",
        consolidation_policy.is_file(),
        "community_artifact_consolidation_policy.json",
        "prior_slices",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    add_check(
        checks,
        defects,
        "prior:artifact_root_layout",
        (monorepo / ARTIFACT_ROOT).name == ".codestrata-artifacts",
        ARTIFACT_ROOT,
        "prior_slices",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    add_check(
        checks,
        defects,
        "prior:assessments_relative",
        ASSESSMENTS_RELATIVE.startswith(ARTIFACT_ROOT),
        ASSESSMENTS_RELATIVE,
        "prior_slices",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    add_check(
        checks,
        defects,
        "prior:validation_relative",
        VALIDATION_RELATIVE.startswith(ARTIFACT_ROOT),
        VALIDATION_RELATIVE,
        "prior_slices",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    return checks, defects
