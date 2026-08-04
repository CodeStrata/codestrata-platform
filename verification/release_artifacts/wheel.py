"""Wheel archive inspection for SV.16."""

from __future__ import annotations

import zipfile
from email.parser import Parser
from io import StringIO
from pathlib import Path

from verification.release_artifacts.models import CheckResult, Defect

_FORBIDDEN_ROOT_PREFIXES = (
    "verification/",
    "platform/",
    "infrastructure/",  # monorepo OpenTofu root — not codestrata.infrastructure
    "tests/",
    "reports/",
    ".git/",
    "codestrata_platform/",
)
_REQUIRED_PREFIX = "codestrata/"


def _wheel_members(wheel_path: Path) -> list[str]:
    with zipfile.ZipFile(wheel_path, "r") as archive:
        return archive.namelist()


def _read_metadata(wheel_path: Path) -> dict[str, str]:
    with zipfile.ZipFile(wheel_path, "r") as archive:
        meta_names = [n for n in archive.namelist() if n.endswith(".dist-info/METADATA")]
        if not meta_names:
            return {}
        raw = archive.read(meta_names[0]).decode("utf-8", errors="replace")
    parser = Parser()
    message = parser.parse(StringIO(raw))
    return {str(k): str(v) for k, v in message.items() if k}


def inspect_wheel(wheel_path: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    label = wheel_path.name

    if not wheel_path.is_file():
        defects.append(
            Defect(
                classification="missing_artifact",
                component="wheel",
                expected="wheel file",
                actual=str(wheel_path.name),
            )
        )
        return checks, defects

    members = _wheel_members(wheel_path)
    # Only root-level archive paths; Engine runtime includes codestrata/infrastructure/.
    forbidden = [
        name
        for name in members
        if any(name.startswith(prefix) for prefix in _FORBIDDEN_ROOT_PREFIXES)
    ]
    has_codestrata = any(name.startswith(_REQUIRED_PREFIX) for name in members)
    has_license = any(
        name.endswith("LICENSE") or name.endswith("license") for name in members
    )

    metadata = _read_metadata(wheel_path)
    license_meta = metadata.get("License") or metadata.get("License-File")
    has_console = False
    for name in members:
        if name.endswith("entry_points.txt"):
            with zipfile.ZipFile(wheel_path, "r") as archive:
                text = archive.read(name).decode("utf-8", errors="replace")
            has_console = "[console_scripts]" in text and "codestrata" in text
            break

    checks.extend(
        [
            CheckResult(
                name=f"wheel:{label}:forbidden_paths",
                ok=not forbidden,
                detail=f"forbidden={forbidden[:5] or 'none'}",
                category="wheel",
            ),
            CheckResult(
                name=f"wheel:{label}:codestrata_package",
                ok=has_codestrata,
                detail=f"members={len(members)}",
                category="wheel",
            ),
            CheckResult(
                name=f"wheel:{label}:license",
                ok=bool(has_license or license_meta),
                detail=f"license_meta={bool(license_meta)} file={has_license}",
                category="wheel",
            ),
            CheckResult(
                name=f"wheel:{label}:console_script",
                ok=has_console,
                detail=f"entry_points={has_console}",
                category="wheel",
            ),
        ]
    )
    if forbidden:
        defects.append(
            Defect(
                classification="forbidden_content",
                component=f"wheel:{label}",
                expected="no monorepo-only paths",
                actual=", ".join(forbidden[:8]),
            )
        )
    if not has_codestrata:
        defects.append(
            Defect(
                classification="missing_package",
                component=f"wheel:{label}",
                expected=_REQUIRED_PREFIX,
                actual="absent",
            )
        )
    return checks, defects


def inspect_wheels(wheel_paths: tuple[str, ...], monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    all_checks: list[CheckResult] = []
    all_defects: list[Defect] = []
    primary = [p for p in wheel_paths if "/a/" in p.replace("\\", "/") and p.endswith(".whl")]
    if not primary:
        primary = [p for p in wheel_paths if p.endswith(".whl")]
    for rel in primary[:1]:
        checks, defects = inspect_wheel(monorepo / rel)
        all_checks.extend(checks)
        all_defects.extend(defects)
    return all_checks, all_defects
