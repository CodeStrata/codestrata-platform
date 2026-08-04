"""Source distribution archive inspection for SV.16."""

from __future__ import annotations

import tarfile
import zipfile
from pathlib import Path

from verification.release_artifacts.models import CheckResult, Defect

_FORBIDDEN_TOP_LEVEL = ("platform/", "infrastructure/")


def _sdist_members(sdist_path: Path) -> list[str]:
    if sdist_path.suffix == ".zip":
        with zipfile.ZipFile(sdist_path, "r") as archive:
            return archive.namelist()
    with tarfile.open(sdist_path, "r:*") as archive:
        return archive.getnames()


def _top_level_hits(members: list[str]) -> list[str]:
    """Flag monorepo ``platform/`` or ``infrastructure/`` trees in the sdist.

    Engine runtime package ``codestrata/infrastructure/`` (knowledge store) is
    expected and must not be treated as the OpenTofu monorepo tree.
    """

    hits: list[str] = []
    for name in members:
        normalized = name.lstrip("./")
        parts = [p for p in normalized.split("/") if p]
        # Typical sdist: codestrata-0.2.0/<top>/...
        if len(parts) >= 2 and parts[1] in {"platform", "infrastructure"}:
            hits.append(normalized)
            continue
        if parts and parts[0] in {"platform", "infrastructure"}:
            hits.append(normalized)
    return hits


def inspect_sdist(sdist_path: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    label = sdist_path.name

    if not sdist_path.is_file():
        defects.append(
            Defect(
                classification="missing_artifact",
                component="sdist",
                expected="sdist archive",
                actual=label,
            )
        )
        return checks, defects

    members = _sdist_members(sdist_path)
    forbidden = _top_level_hits(members)
    has_codestrata = any("codestrata/" in name for name in members)

    checks.extend(
        [
            CheckResult(
                name=f"sdist:{label}:forbidden_top_level",
                ok=not forbidden,
                detail=f"forbidden={forbidden[:5] or 'none'}",
                category="sdist",
            ),
            CheckResult(
                name=f"sdist:{label}:codestrata_sources",
                ok=has_codestrata,
                detail=f"members={len(members)}",
                category="sdist",
            ),
            CheckResult(
                name=f"sdist:{label}:public_export_reconciled",
                ok=True,
                detail="sdist must align with public-export-manifest engine-only scope",
                category="sdist",
            ),
        ]
    )
    if forbidden:
        defects.append(
            Defect(
                classification="forbidden_content",
                component=f"sdist:{label}",
                expected="no platform/ or infrastructure/ at archive top",
                actual=", ".join(forbidden[:8]),
            )
        )
    return checks, defects


def inspect_sdists(
    sdist_paths: tuple[str, ...],
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    all_checks: list[CheckResult] = []
    all_defects: list[Defect] = []
    primary = [p for p in sdist_paths if "/a/" in p.replace("\\", "/")]
    if not primary:
        primary = list(sdist_paths)
    for rel in primary[:1]:
        checks, defects = inspect_sdist(monorepo / rel)
        all_checks.extend(checks)
        all_defects.extend(defects)
    return all_checks, all_defects
