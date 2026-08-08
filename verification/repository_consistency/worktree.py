"""Worktree hygiene classification."""

from __future__ import annotations

import subprocess
from pathlib import Path

from verification.repository_consistency.inventory import add_check
from verification.repository_consistency.models import CheckResult, Defect

UNEXPECTED_MARKERS = (
    ".vsix",
    "/dist/",
    "/coverage/",
    "/.terraform/",
    "__pycache__",
    ".export-staging",
    "export-staging/",
)


def check_worktree(monorepo: Path) -> tuple[list[CheckResult], list[Defect], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    residue: list[str] = []

    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain", "-u"],
            cwd=monorepo,
            capture_output=True,
            text=True,
            check=False,
        )
        lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
    except Exception as exc:  # noqa: BLE001
        add_check(checks, defects, "worktree:git_status", False, str(type(exc).__name__), "worktree")
        return checks, defects, residue

    add_check(checks, defects, "worktree:git_status", True, f"entries={len(lines)}", "worktree")

    unexpected = []
    for ln in lines:
        path = ln[3:].strip() if len(ln) > 3 else ln
        lower = path.lower()
        if any(m in lower for m in UNEXPECTED_MARKERS):
            # allow ignored patterns that shouldn't appear; if they do, flag
            unexpected.append(path)
        # classify epic16 paths as expected during this slice
        if "repository_consistency" in path or "sv16-8" in path or "repository_consistency_policy" in path:
            continue
        if path.endswith(".DS_Store"):
            unexpected.append(path)

    residue = unexpected
    add_check(
        checks,
        defects,
        "worktree:no_unexplained_build_residue",
        not unexpected,
        ",".join(unexpected[:10]) or "none",
        "worktree",
    )

    # Known allowed: uncommitted epic16 work itself
    add_check(
        checks,
        defects,
        "worktree:uncommitted_allowed_limitation",
        True,
        "worktree_uncommitted_by_design",
        "worktree",
    )
    return checks, defects, residue
