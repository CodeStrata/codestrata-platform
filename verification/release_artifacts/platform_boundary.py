"""Ensure Community wheel/sdist excludes Platform package."""

from __future__ import annotations

import tarfile
import zipfile
from pathlib import Path

from verification.release_artifacts.models import CheckResult, Defect


def _archive_contains_platform(path: Path) -> bool:
    needle = "codestrata_platform"
    if path.suffix == ".whl":
        with zipfile.ZipFile(path, "r") as archive:
            return any(needle in name for name in archive.namelist())
    if path.name.endswith(".tar.gz"):
        with tarfile.open(path, "r:*") as archive:
            return any(needle in member.name for member in archive.getmembers())
    return False


def check_platform_boundary(
    monorepo: Path,
    *,
    wheel_relative: str | None,
    sdist_relative: str | None,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    for label, rel in (("wheel", wheel_relative), ("sdist", sdist_relative)):
        if not rel:
            continue
        path = monorepo / rel
        hit = _archive_contains_platform(path)
        checks.append(
            CheckResult(
                name=f"platform_boundary:{label}:no_codestrata_platform",
                ok=not hit,
                detail=f"artifact={rel}",
                category="platform_boundary",
            )
        )
        if hit:
            defects.append(
                Defect(
                    classification="platform_leak",
                    component=label,
                    expected="no codestrata_platform in Community artifact",
                    actual="codestrata_platform present",
                )
            )

    return checks, defects
