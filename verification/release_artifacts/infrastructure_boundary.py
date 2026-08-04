"""Infrastructure boundary checks for release artifacts."""

from __future__ import annotations

import zipfile
from pathlib import Path

from verification.release_artifacts.models import CheckResult, Defect


def _infra_state_hits(infra_root: Path) -> list[str]:
    hits: list[str] = []
    if not infra_root.is_dir():
        return hits
    for path in infra_root.rglob("*"):
        if not path.is_file():
            continue
        name = path.name
        if name.endswith(".tfstate") or name.endswith(".tfplan"):
            hits.append(str(path.relative_to(infra_root)))
    return hits


def _wheel_contains_infra(wheel_path: Path) -> bool:
    """Detect monorepo ``infrastructure/`` tree — not Engine ``codestrata.infrastructure``."""

    with zipfile.ZipFile(wheel_path, "r") as archive:
        return any(name.startswith("infrastructure/") for name in archive.namelist())


def check_infrastructure_boundary(
    monorepo: Path,
    *,
    wheel_relative: str | None,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    infra_root = monorepo / "infrastructure"
    state_hits = _infra_state_hits(infra_root)
    checks.append(
        CheckResult(
            name="infrastructure_boundary:no_tfstate_tfplan",
            ok=not state_hits,
            detail=f"hits={state_hits[:5] or 'none'}",
            category="infrastructure_boundary",
        )
    )
    if state_hits:
        defects.append(
            Defect(
                classification="forbidden_infra_state",
                component="infrastructure/",
                expected="no .tfstate/.tfplan tracked in tree",
                actual=", ".join(state_hits[:8]),
            )
        )

    if wheel_relative:
        wheel = monorepo / wheel_relative
        if wheel.is_file():
            leaked = _wheel_contains_infra(wheel)
            checks.append(
                CheckResult(
                    name="infrastructure_boundary:wheel_excludes_infra",
                    ok=not leaked,
                    detail=f"wheel={wheel_relative}",
                    category="infrastructure_boundary",
                )
            )
            if leaked:
                defects.append(
                    Defect(
                        classification="infra_leak",
                        component="wheel",
                        expected="infrastructure excluded from wheel",
                        actual="infrastructure paths present",
                    )
                )

    return checks, defects
