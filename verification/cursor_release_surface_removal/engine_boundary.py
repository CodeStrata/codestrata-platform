"""Engine and Platform release-boundary checks for Slice 12.2."""

from __future__ import annotations

from pathlib import Path

from verification.cursor_release_surface_removal.models import CheckResult, Defect


def check_engine_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    engine_py = monorepo / "engine" / "pyproject.toml"
    text = engine_py.read_text(encoding="utf-8") if engine_py.is_file() else ""
    version_ok = 'version = "0.2.0"' in text
    checks.append(
        CheckResult(
            name="engine:release_version_unchanged",
            ok=version_ok,
            detail="engine pyproject remains 0.2.0",
            category="engine",
        )
    )
    if not version_ok:
        defects.append(
            Defect(
                "Engine/Platform release-boundary defect",
                "engine/pyproject.toml",
                "0.2.0",
                "changed",
            )
        )
    assessment_ok = False
    for rel in (
        "engine/src/codestrata/reporting/contract/constants.py",
        "engine/src/codestrata/reporting/contract/identifiers.py",
    ):
        path = monorepo / rel
        if path.is_file() and "1.2" in path.read_text(encoding="utf-8", errors="ignore"):
            assessment_ok = True
            break
    checks.append(
        CheckResult(
            name="engine:assessment_schema_1_2",
            ok=assessment_ok,
            detail="Assessment schema 1.2 pin present",
            category="engine",
        )
    )
    return checks, defects


def check_platform_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    platform_py = monorepo / "platform" / "pyproject.toml"
    present = platform_py.is_file()
    checks.append(
        CheckResult(
            name="platform:pyproject_present",
            ok=present,
            detail=f"present={present}",
            category="platform",
        )
    )
    # Independent version posture: Platform may differ; just ensure file still exists.
    infra = monorepo / "infrastructure"
    checks.append(
        CheckResult(
            name="platform:infrastructure_unchanged_presence",
            ok=infra.is_dir(),
            detail="infrastructure directory present (export redesign not started)",
            category="platform",
        )
    )
    return checks, defects
