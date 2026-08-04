"""Git worktree classification for release artifact verification."""

from __future__ import annotations

import subprocess
from enum import StrEnum
from pathlib import Path

from verification.release_artifacts.models import CheckResult, Warning


class GitWorktreeClass(StrEnum):
    CLEAN = "clean"
    EXPECTED_UNCOMMITTED_RELEASE_CHANGES = "expected_uncommitted_release_changes"
    UNEXPECTED_GENERATED_FILES = "unexpected_generated_files"
    DIRTY_OTHER = "dirty_other"


_FORBIDDEN_TRACKED_SUFFIXES = (".tfstate", ".tfplan")
_FORBIDDEN_TRACKED_NAMES = ("credentials.json", "credentials.yaml", "credentials.yml")


def _run_git(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )


def _branch_name(monorepo: Path) -> str:
    result = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=monorepo)
    return (result.stdout or "").strip() or "unknown"


def _short_head(monorepo: Path) -> str:
    result = _run_git(["rev-parse", "--short", "HEAD"], cwd=monorepo)
    return (result.stdout or "").strip() or "unknown"


def _is_dirty(monorepo: Path) -> bool:
    result = _run_git(["status", "--porcelain"], cwd=monorepo)
    return bool((result.stdout or "").strip())


def _tracked_forbidden_files(monorepo: Path) -> list[str]:
    result = _run_git(["ls-files"], cwd=monorepo)
    hits: list[str] = []
    for line in (result.stdout or "").splitlines():
        rel = line.strip()
        if not rel:
            continue
        name = Path(rel).name.lower()
        if any(rel.endswith(suffix) for suffix in _FORBIDDEN_TRACKED_SUFFIXES):
            hits.append(rel)
        elif name in _FORBIDDEN_TRACKED_NAMES:
            hits.append(rel)
    return hits


def classify_worktree(monorepo: Path) -> tuple[GitWorktreeClass, str, str, list[str]]:
    branch = _branch_name(monorepo)
    head = _short_head(monorepo)
    forbidden = _tracked_forbidden_files(monorepo)
    if forbidden:
        return GitWorktreeClass.UNEXPECTED_GENERATED_FILES, branch, head, forbidden
    if not _is_dirty(monorepo):
        return GitWorktreeClass.CLEAN, branch, head, []
    if branch.startswith("release/v0.2.0"):
        return GitWorktreeClass.EXPECTED_UNCOMMITTED_RELEASE_CHANGES, branch, head, []
    return GitWorktreeClass.DIRTY_OTHER, branch, head, []


def check_git_state(monorepo: Path) -> tuple[list[CheckResult], list[Warning]]:
    classification, branch, head, forbidden = classify_worktree(monorepo)
    checks = [
        CheckResult(
            name="git:branch_readable",
            ok=branch != "unknown",
            detail=f"branch={branch}",
            category="git_state",
        ),
        CheckResult(
            name="git:head_readable",
            ok=head != "unknown",
            detail=f"head={head}",
            category="git_state",
        ),
        CheckResult(
            name="git:no_forbidden_tracked_files",
            ok=classification != GitWorktreeClass.UNEXPECTED_GENERATED_FILES,
            detail=f"forbidden={forbidden or 'none'}",
            category="git_state",
        ),
        CheckResult(
            name="git:worktree_classification",
            ok=classification
            in {
                GitWorktreeClass.CLEAN,
                GitWorktreeClass.EXPECTED_UNCOMMITTED_RELEASE_CHANGES,
                GitWorktreeClass.DIRTY_OTHER,
            },
            detail=f"classification={classification.value}",
            category="git_state",
        ),
        CheckResult(
            name="git:never_require_clean_worktree",
            ok=True,
            detail="dirty worktree allowed; classification recorded only",
            category="git_state",
        ),
    ]
    warnings: list[Warning] = []
    if classification == GitWorktreeClass.EXPECTED_UNCOMMITTED_RELEASE_CHANGES:
        warnings.append(
            Warning(
                code="expected_uncommitted_release_changes",
                detail=f"branch={branch} has uncommitted release changes",
            )
        )
    elif classification == GitWorktreeClass.DIRTY_OTHER:
        warnings.append(
            Warning(
                code="dirty_worktree",
                detail=f"branch={branch} is dirty outside release/v0.2.0*",
            )
        )
    elif classification == GitWorktreeClass.UNEXPECTED_GENERATED_FILES:
        warnings.append(
            Warning(
                code="unexpected_generated_files",
                detail=f"tracked forbidden files: {', '.join(forbidden[:5])}",
                release_impact="blocking",
            )
        )
    return checks, warnings
