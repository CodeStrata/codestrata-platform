"""Read and compare release version markers across monorepo surfaces."""

from __future__ import annotations

import json
import re
from pathlib import Path

from verification.release_artifacts.contract import INTENDED_RELEASE_VERSION
from verification.release_artifacts.models import CheckResult, Defect, Warning

_PYPROJECT_VERSION_RE = re.compile(
    r'^\s*version\s*=\s*["\']([^"\']+)["\']',
    re.MULTILINE,
)


def _read_pyproject_version(path: Path) -> str | None:
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    match = _PYPROJECT_VERSION_RE.search(text)
    return match.group(1) if match else None


def _read_package_json_version(path: Path) -> str | None:
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    version = data.get("version")
    return str(version) if version else None


def read_versions(monorepo: Path) -> dict[str, str | None]:
    init_text = ""
    init_path = monorepo / "engine" / "src" / "codestrata" / "__init__.py"
    if init_path.is_file():
        init_text = init_path.read_text(encoding="utf-8")
    init_match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', init_text)
    return {
        "engine": _read_pyproject_version(monorepo / "engine" / "pyproject.toml"),
        "engine_module": init_match.group(1) if init_match else None,
        "platform": _read_pyproject_version(monorepo / "platform" / "pyproject.toml"),
        "workspace": _read_pyproject_version(monorepo / "pyproject.toml"),
        "vscode": _read_package_json_version(monorepo / "vscode-plugin" / "package.json"),
        "cursor": _read_package_json_version(monorepo / "cursor-plugin" / "package.json"),
    }


def check_versions(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], list[Warning]]:
    versions = read_versions(monorepo)
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    warnings: list[Warning] = []

    engine = versions.get("engine")
    checks.append(
        CheckResult(
            name="versions:engine_present",
            ok=bool(engine),
            detail=f"engine={engine or '<missing>'}",
            category="versions",
        )
    )
    if engine != INTENDED_RELEASE_VERSION:
        defects.append(
            Defect(
                classification="version_mismatch",
                component="engine/pyproject.toml",
                expected=INTENDED_RELEASE_VERSION,
                actual=str(engine or "<missing>"),
                detail="Engine Community package version must match intended release",
            )
        )
    checks.append(
        CheckResult(
            name="versions:engine_matches_intended",
            ok=engine == INTENDED_RELEASE_VERSION,
            detail=f"engine={engine} intended={INTENDED_RELEASE_VERSION}",
            category="versions",
        )
    )

    engine_module = versions.get("engine_module")
    if engine and engine_module and engine != engine_module:
        defects.append(
            Defect(
                classification="version_mismatch",
                component="engine/src/codestrata/__init__.py",
                expected=str(engine),
                actual=str(engine_module),
                detail="Engine module __version__ must match pyproject version",
            )
        )
    checks.append(
        CheckResult(
            name="versions:engine_module_matches_pyproject",
            ok=bool(engine) and engine == engine_module,
            detail=f"pyproject={engine} module={engine_module}",
            category="versions",
        )
    )

    platform = versions.get("platform")
    checks.append(
        CheckResult(
            name="versions:platform_present",
            ok=bool(platform),
            detail=f"platform={platform or '<missing>'}",
            category="versions",
        )
    )
    if platform and platform != INTENDED_RELEASE_VERSION:
        warnings.append(
            Warning(
                code="platform_version_independent",
                detail=(
                    f"Platform version {platform} may differ from Engine "
                    f"{INTENDED_RELEASE_VERSION}; Platform is not published as Community."
                ),
            )
        )
    checks.append(
        CheckResult(
            name="versions:platform_documented_independent",
            ok=True,
            detail="Platform version is independent of Community Engine release",
            category="versions",
        )
    )

    for label in ("workspace", "vscode", "cursor"):
        value = versions.get(label)
        checks.append(
            CheckResult(
                name=f"versions:{label}_readable",
                ok=value is not None,
                detail=f"{label}={value or '<missing>'}",
                category="versions",
            )
        )

    vscode = versions.get("vscode")
    cursor = versions.get("cursor")
    if vscode and vscode != INTENDED_RELEASE_VERSION:
        defects.append(
            Defect(
                classification="version_mismatch",
                component="vscode-plugin/package.json",
                expected=INTENDED_RELEASE_VERSION,
                actual=vscode,
                release_impact="blocking",
            )
        )
    if cursor and cursor != INTENDED_RELEASE_VERSION:
        defects.append(
            Defect(
                classification="version_mismatch",
                component="cursor-plugin/package.json",
                expected=INTENDED_RELEASE_VERSION,
                actual=cursor,
                release_impact="blocking",
            )
        )

    return checks, defects, warnings
