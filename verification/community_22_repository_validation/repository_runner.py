"""Repository clone and assessment runner helpers."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from verification.community_22_repository_validation.assessment import (
    assessment_output_dir,
    classify_assessment_status,
)
from verification.community_22_repository_validation.catalog import CatalogRepository
from verification.community_22_repository_validation.contract import ASSESSMENTS_RELATIVE


def _ensure_engine_verification_path(monorepo: Path) -> None:
    engine = str((monorepo / "engine").resolve())
    if engine not in sys.path:
        sys.path.append(engine)
    import verification as verification_pkg
    from pkgutil import extend_path

    verification_pkg.__path__ = extend_path(list(verification_pkg.__path__), verification_pkg.__name__)


def git_isolation_env() -> dict[str, str]:
    """Avoid global/system git insteadOf PAT substitution during clones."""

    return {
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_SYSTEM": "/dev/null",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_LFS_SKIP_SMUDGE": "1",
    }


@dataclass(frozen=True, slots=True)
class RepositoryRunResult:
    repository_validation_id: str
    clone_status: str
    assessment_status: str
    output_dir: str
    detail: str


def _to_sv4_catalog_entry(repo: CatalogRepository):
    _ensure_engine_verification_path(Path(__file__).resolve().parents[2])
    from verification.repository_assessment.catalog import CatalogEntry, QualifiedRevision

    return CatalogEntry(
        id=repo.repository_id,
        project_name=repo.project_name,
        github_repository=repo.github_repository,
        github_url=repo.github_url,
        language_group=str(repo.language_group or ""),
        candidate_category=str(repo.raw.get("candidate_category") or ""),
        license=str(repo.raw.get("license") or ""),
        qualified_revision=QualifiedRevision(
            revision_type=repo.qualified_revision_type,
            value=repo.qualified_revision_value,
            source_tag=repo.qualified_revision_source_tag,
        ),
        enabled_for_smoke=bool(repo.enabled_for.get("smoke")),
        selection_reason="sv17-13_release_validation",
    )


def clone_repository(
    monorepo: Path,
    repo: CatalogRepository,
    destination: Path,
    *,
    timeout_s: int = 600,
) -> tuple[bool, str]:
    _ensure_engine_verification_path(monorepo)
    from verification.repository_assessment.clone import clone_qualified_repository
    from verification.repository_assessment.workspace import assert_outside_codestrata_tree

    assert_outside_codestrata_tree(destination, monorepo)
    entry = _to_sv4_catalog_entry(repo)
    env = {**os.environ, **git_isolation_env()}
    previous = os.environ.copy()
    try:
        os.environ.update(env)
        result = clone_qualified_repository(entry, destination, timeout_s=timeout_s)
    finally:
        os.environ.clear()
        os.environ.update(previous)
    return result.ok, result.detail


def record_repository_result(
    monorepo: Path,
    repo: CatalogRepository,
    *,
    skip_execute: bool,
    clone_ok: bool | None = None,
    clone_detail: str = "",
) -> dict[str, Any]:
    run_dir = assessment_output_dir(monorepo, repo.repository_id)
    if skip_execute:
        return {
            "repository_validation_id": repo.repository_id,
            "language": repo.language_group,
            "ecosystem": repo.ecosystem,
            "assessment_status": "not_executed",
            "head_status_summary": "not_executed",
            "report_status": "not_executed",
            "eir_eligible": bool(repo.enabled_for.get("engineering_intelligence")),
            "telemetry_status": "not_executed",
            "defect_count": 0,
            "limitations": ["full_22_repository_suite_not_executed"],
        }

    assessment_status = classify_assessment_status(run_dir)
    return {
        "repository_validation_id": repo.repository_id,
        "language": repo.language_group,
        "ecosystem": repo.ecosystem,
        "assessment_status": assessment_status,
        "head_status_summary": "unknown" if assessment_status == "not_executed" else "pending_verification",
        "report_status": assessment_status,
        "eir_eligible": bool(repo.enabled_for.get("engineering_intelligence")),
        "telemetry_status": "not_executed",
        "defect_count": 0 if clone_ok is not False else 1,
        "limitations": [] if clone_ok is not False else [clone_detail or "clone_failed"],
    }


def run_repositories(
    monorepo: Path,
    repositories: tuple[CatalogRepository, ...],
    *,
    skip_execute: bool,
    clone_root: Path | None = None,
) -> tuple[list[RepositoryRunResult], list[dict[str, Any]]]:
    """Clone/assess repositories unless skip_execute is set."""

    results: list[RepositoryRunResult] = []
    register_entries: list[dict[str, Any]] = []
    assessments_root = monorepo / ASSESSMENTS_RELATIVE
    assessments_root.mkdir(parents=True, exist_ok=True)

    if skip_execute:
        for repo in repositories:
            entry = record_repository_result(monorepo, repo, skip_execute=True)
            register_entries.append(entry)
            results.append(
                RepositoryRunResult(
                    repository_validation_id=repo.repository_id,
                    clone_status="skipped",
                    assessment_status="not_executed",
                    output_dir=str(assessment_output_dir(monorepo, repo.repository_id).relative_to(monorepo)),
                    detail="skip_execute",
                )
            )
        return results, register_entries

    temp_root = clone_root or (monorepo / ".codestrata-artifacts/temporary/sv17-13-clones")
    temp_root.mkdir(parents=True, exist_ok=True)
    for repo in repositories:
        dest = temp_root / repo.repository_id
        ok, detail = clone_repository(monorepo, repo, dest)
        entry = record_repository_result(
            monorepo,
            repo,
            skip_execute=False,
            clone_ok=ok,
            clone_detail=detail,
        )
        register_entries.append(entry)
        results.append(
            RepositoryRunResult(
                repository_validation_id=repo.repository_id,
                clone_status="pass" if ok else "fail",
                assessment_status=entry["assessment_status"],
                output_dir=str(assessment_output_dir(monorepo, repo.repository_id).relative_to(monorepo)),
                detail=detail if not ok else "cloned",
            )
        )
    return results, register_entries
