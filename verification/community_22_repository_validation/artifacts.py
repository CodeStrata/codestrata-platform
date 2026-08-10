"""Artifact root layout checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_22_repository_validation.contract import (
    ARTIFACT_ROOT,
    ASSESSMENTS_RELATIVE,
    INTELLIGENCE_RELATIVE,
    SV1713_OUTPUT_RELATIVE,
    VALIDATION_RELATIVE,
)
from verification.community_22_repository_validation.helpers import add_check
from verification.community_22_repository_validation.models import CheckResult, Defect


def check_artifacts(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    layout = {
        "artifact_root": ARTIFACT_ROOT,
        "assessments": ASSESSMENTS_RELATIVE,
        "intelligence": INTELLIGENCE_RELATIVE,
        "validation": VALIDATION_RELATIVE,
        "suite_output": SV1713_OUTPUT_RELATIVE,
    }

    for key, rel in layout.items():
        add_check(
            checks,
            defects,
            f"artifacts:{key}",
            rel.startswith(ARTIFACT_ROOT) or key == "artifact_root",
            rel,
            "artifacts",
            CheckResult=CheckResult,
            Defect=Defect,
        )

    suite_dir = monorepo / SV1713_OUTPUT_RELATIVE
    add_check(
        checks,
        defects,
        "artifacts:suite_dir_relative",
        str(suite_dir).startswith(str(monorepo / ARTIFACT_ROOT)),
        SV1713_OUTPUT_RELATIVE,
        "artifacts",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    return checks, defects, layout
