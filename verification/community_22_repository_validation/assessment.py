"""Assessment artifact checks for Slice 17.13."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_22_repository_validation.catalog import CatalogRepository
from verification.community_22_repository_validation.contract import ASSESSMENTS_RELATIVE
from verification.community_22_repository_validation.helpers import add_check
from verification.community_22_repository_validation.models import CheckResult, Defect


def assessments_root(monorepo: Path) -> Path:
    return monorepo / ASSESSMENTS_RELATIVE


def assessment_output_dir(monorepo: Path, repository_id: str) -> Path:
    """Compatibility helper — returns assessments root / repository_id marker path."""

    return assessments_root(monorepo) / repository_id


def find_assessment_runs(monorepo: Path, repository_id: str) -> list[Path]:
    root = assessments_root(monorepo)
    if not root.is_dir():
        return []
    slug = repository_id.strip().lower()
    prefix = f"{slug}-"
    runs = [
        child
        for child in root.iterdir()
        if child.is_dir() and child.name.startswith(prefix)
    ]
    return sorted(runs, key=lambda p: p.name, reverse=True)


def classify_assessment_status(run_dir: Path | None) -> str:
    if run_dir is None or not run_dir.is_dir():
        return "not_executed"
    manifest = run_dir / "assessment.json"
    html = run_dir / "assessment.html"
    if manifest.is_file() and html.is_file():
        return "present"
    if manifest.is_file() or html.is_file():
        return "incomplete"
    return "incomplete"


def check_assessment_layout(
    monorepo: Path,
    repositories: tuple[CatalogRepository, ...],
    *,
    skip_execute: bool,
) -> tuple[list[CheckResult], list[Defect], list[dict[str, Any]]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    results: list[dict[str, Any]] = []

    add_check(
        checks,
        defects,
        "assessment:output_root",
        ASSESSMENTS_RELATIVE.startswith(".codestrata-artifacts/"),
        ASSESSMENTS_RELATIVE,
        "assessment",
        CheckResult=CheckResult,
        Defect=Defect,
    )

    for repo in repositories:
        runs = find_assessment_runs(monorepo, repo.repository_id)
        run_dir = runs[0] if runs else None
        status = classify_assessment_status(run_dir)
        if skip_execute:
            ok = status in {"not_executed", "present"}
            detail = status
            recorded = "not_executed"
        else:
            # After suite execution: each catalog repo must have present artifacts.
            ok = status == "present"
            detail = f"{status};runs={len(runs)}"
            recorded = status if status == "present" else status
            if status != "present":
                # Keep recorded status honest for register / EIR eligibility.
                recorded = status
        add_check(
            checks,
            defects,
            f"assessment:status:{repo.repository_id}",
            ok,
            detail,
            "assessment",
            CheckResult=CheckResult,
            Defect=Defect,
        )
        results.append(
            {
                "repository_validation_id": repo.repository_id,
                "language": repo.language_group,
                "ecosystem": repo.ecosystem,
                "assessment_status": recorded,
                "report_status": recorded,
                "defect_count": 0,
                "limitations": ["full_22_repository_suite_not_executed"] if skip_execute else [],
                "assessment_run_id": run_dir.name if run_dir is not None else None,
                "assessment_artifact_ref": (
                    f"{ASSESSMENTS_RELATIVE}/{run_dir.name}" if run_dir is not None else None
                ),
            }
        )

    return checks, defects, results
