"""Build / package / Marketplace / release / version / checksum / license / publish / CI checks."""

from __future__ import annotations

import json
import re
from pathlib import Path

from verification.cursor_release_surface_removal.contract import (
    ACTIVE_EDITOR_EXTENSIONS,
    EXPECTED_VSCODE_PACKAGE_NAME,
    EXPECTED_VSCODE_VERSION,
)
from verification.cursor_release_surface_removal.inventory import REMOVED_ACTIVE_SURFACES
from verification.cursor_release_surface_removal.models import CheckResult, Defect

_CURSOR_TOKENS = ("cursor-plugin", "codestrata-cursor", "check_cursor_extension")


def _status(checks: list[CheckResult]) -> str:
    if not checks:
        return "not_executed"
    return "pass" if all(c.ok for c in checks) else "fail"


def check_build_surfaces(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    hits: list[str] = []
    release = monorepo / "scripts" / "release"
    if release.is_dir():
        for child in release.rglob("*.py"):
            text = child.read_text(encoding="utf-8", errors="ignore")
            if "cursor-plugin" in text or "codestrata-cursor" in text:
                hits.append(str(child.relative_to(monorepo)))
    checks.append(
        CheckResult(
            name="build:no_cursor_plugin_entry",
            ok=not hits,
            detail=f"hits={sorted(set(hits))[:8] or 'none'}",
            category="build",
        )
    )
    if hits:
        defects.append(
            Defect("build-surface defect", "scripts", "no cursor-plugin entry", ",".join(hits[:5]))
        )
    checks.append(
        CheckResult(
            name="build:cursor_plugin_directory_absent",
            ok=not (monorepo / "cursor-plugin").exists(),
            detail="cursor-plugin absent",
            category="build",
        )
    )
    return checks, defects


def check_package_surfaces(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    deps = (monorepo / "scripts" / "release" / "dependencies.py").read_text(encoding="utf-8")
    ok = "codestrata-cursor" not in deps and "cursor-plugin/package.json" not in deps
    checks.append(
        CheckResult(
            name="package:dependency_inventory_vscode_only",
            ok=ok,
            detail="codestrata-cursor absent from dependency inventory",
            category="package",
        )
    )
    if not ok:
        defects.append(
            Defect("package-surface defect", "dependencies.py", "vscode-only", "cursor present")
        )
    module = monorepo / "verification" / "release_artifacts" / "cursor_extension.py"
    checks.append(
        CheckResult(
            name="package:cursor_extension_module_removed",
            ok=not module.exists(),
            detail=f"absent={not module.exists()}",
            category="package",
        )
    )
    if module.exists():
        defects.append(
            Defect(
                "package-surface defect",
                "cursor_extension.py",
                "absent",
                "present",
            )
        )
    return checks, defects


def check_marketplace_surfaces(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    paths = (
        monorepo / "governance" / "assets" / "extension-branding" / "MARKETPLACE_PUBLICATION.md",
        monorepo / "vscode-plugin" / "MARKETPLACE.md",
    )
    for path in paths:
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        bad = (
            "codestrata-cursor" in text
            or "cursor-plugin" in text
            or "npx ovsx publish codestrata-cursor" in text
            or "both plugins" in text.lower()
        )
        rel = str(path.relative_to(monorepo)) if path.is_file() else path.name
        checks.append(
            CheckResult(
                name=f"marketplace:no_cursor_publish:{path.name}",
                ok=not bad and path.is_file(),
                detail=f"file={rel};cursor_publish_absent={not bad}",
                category="marketplace",
            )
        )
        if bad or not path.is_file():
            defects.append(
                Defect(
                    "Marketplace-surface defect",
                    rel,
                    "VS Code-only publish instructions",
                    "cursor publish remains" if bad else "missing",
                )
            )
    return checks, defects


def check_release_inventory(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    inventory = (monorepo / "scripts" / "release" / "inventory.py").read_text(encoding="utf-8")
    ok_surface = '"cursor-plugin/"' not in inventory and "'cursor-plugin/'" not in inventory
    checks.append(
        CheckResult(
            name="release_inventory:no_cursor_surface",
            ok=ok_surface,
            detail="cursor-plugin surface absent from SURFACE_CLASSIFICATIONS",
            category="release_inventory",
        )
    )
    if not ok_surface:
        defects.append(
            Defect(
                "release-inventory defect",
                "inventory.py",
                "no cursor-plugin surface",
                "present",
            )
        )

    manifest = (monorepo / "public-export-manifest.yaml").read_text(encoding="utf-8")
    ok_export = "  - name: codestrata-cursor" not in manifest
    checks.append(
        CheckResult(
            name="release_inventory:no_cursor_export",
            ok=ok_export,
            detail="codestrata-cursor export entry absent",
            category="release_inventory",
        )
    )
    if not ok_export:
        defects.append(
            Defect(
                "release-inventory defect",
                "public-export-manifest.yaml",
                "no codestrata-cursor export",
                "present",
            )
        )

    surface_doc = monorepo / "governance" / "release" / "RELEASE_SURFACE_INVENTORY.md"
    text = surface_doc.read_text(encoding="utf-8") if surface_doc.is_file() else ""
    ok_doc = "codestrata-cursor" not in text and "`cursor-plugin/`" not in text
    checks.append(
        CheckResult(
            name="release_inventory:surface_doc_vscode_only",
            ok=ok_doc,
            detail="RELEASE_SURFACE_INVENTORY has no Cursor rows",
            category="release_inventory",
        )
    )
    if not ok_doc:
        defects.append(
            Defect(
                "release-inventory defect",
                "RELEASE_SURFACE_INVENTORY.md",
                "vscode-only",
                "cursor rows",
            )
        )

    checks.append(
        CheckResult(
            name="release_inventory:active_editor_extensions",
            ok=list(ACTIVE_EDITOR_EXTENSIONS) == ["codestrata-vscode"],
            detail=f"active={list(ACTIVE_EDITOR_EXTENSIONS)}",
            category="release_inventory",
        )
    )
    return checks, defects


def check_release_artifacts(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    runner = (monorepo / "verification" / "release_artifacts" / "runner.py").read_text(
        encoding="utf-8"
    )
    ok = "check_cursor_extension" not in runner and "cursor_extension" not in runner
    checks.append(
        CheckResult(
            name="release_artifacts:runner_has_no_cursor_check",
            ok=ok,
            detail="SV.16 runner does not invoke Cursor packaging checks",
            category="release_artifacts",
        )
    )
    if not ok:
        defects.append(
            Defect(
                "artifact-verification defect",
                "release_artifacts/runner.py",
                "no cursor checks",
                "cursor check remains",
            )
        )
    versions_mod = (monorepo / "verification" / "release_artifacts" / "versions.py").read_text(
        encoding="utf-8"
    )
    ok_v = "cursor-plugin" not in versions_mod and '"cursor"' not in versions_mod
    checks.append(
        CheckResult(
            name="release_artifacts:versions_matrix_vscode_only",
            ok=ok_v,
            detail="version matrix excludes Cursor",
            category="release_artifacts",
        )
    )
    if not ok_v:
        defects.append(
            Defect(
                "artifact-verification defect",
                "versions.py",
                "no cursor key",
                "cursor key present",
            )
        )
    return checks, defects


def check_versions_surface(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    text = (monorepo / "scripts" / "release" / "versions.py").read_text(encoding="utf-8")
    ok = "cursor_extension" not in text and "cursor-plugin" not in text
    checks.append(
        CheckResult(
            name="versions:no_cursor_expectation",
            ok=ok,
            detail="check_version_consistency is VS Code-only for extensions",
            category="versions",
        )
    )
    if not ok:
        defects.append(
            Defect("version-alignment defect", "scripts/release/versions.py", "no cursor", "present")
        )
    return checks, defects


def check_checksums_and_licensing(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    lic = (monorepo / "scripts" / "release" / "licensing.py").read_text(encoding="utf-8")
    ok = "cursor-plugin" not in lic
    checks.append(
        CheckResult(
            name="licensing:no_cursor_package_check",
            ok=ok,
            detail="license inventory checks vscode-plugin only",
            category="licensing",
        )
    )
    if not ok:
        defects.append(
            Defect("licensing defect", "licensing.py", "vscode-only", "cursor-plugin present")
        )
    checksums = monorepo / "scripts" / "release" / "checksums.py"
    text = checksums.read_text(encoding="utf-8") if checksums.is_file() else ""
    ok_c = "cursor-plugin" not in text and "codestrata-cursor" not in text
    checks.append(
        CheckResult(
            name="checksums:no_cursor_artifact_names",
            ok=ok_c,
            detail="checksum helpers have no Cursor artifact names",
            category="checksums",
        )
    )
    return checks, defects


def check_publishing(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    hardening = monorepo / "governance" / "release" / "EXTRACTION_HARDENING.md"
    text = hardening.read_text(encoding="utf-8") if hardening.is_file() else ""
    ok = "CodeStrata/codestrata-cursor" not in text and "cursor-plugin/EXTRACTION" not in text
    checks.append(
        CheckResult(
            name="publishing:extraction_hardening_vscode_only",
            ok=ok,
            detail="EXTRACTION_HARDENING has no active Cursor destination",
            category="publishing",
        )
    )
    if not ok:
        defects.append(
            Defect(
                "publishing defect",
                "EXTRACTION_HARDENING.md",
                "no codestrata-cursor destination",
                "present",
            )
        )
    return checks, defects


def check_ci_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    workflows = monorepo / ".github" / "workflows"
    hits: list[str] = []
    if workflows.is_dir():
        for path in list(workflows.rglob("*.yml")) + list(workflows.rglob("*.yaml")):
            text = path.read_text(encoding="utf-8", errors="ignore")
            # Active Cursor jobs/steps are forbidden. Negative assertions that Cursor
            # export trees are absent (Slice 12.9) are allowed.
            if re.search(
                r"working-directory:\s*cursor-plugin|cursor-ci|cursor-package|"
                r"name:\s*cursor[\w-]*\s*$",
                text,
                re.IGNORECASE | re.M,
            ):
                hits.append(str(path.relative_to(monorepo)))
                continue
            # cursor-plugin path as an active build root
            if "cursor-plugin/" in text and "test ! -d" not in text:
                hits.append(str(path.relative_to(monorepo)))
    checks.append(
        CheckResult(
            name="ci:no_cursor_in_root_workflows",
            ok=not hits,
            detail=f"hits={hits or 'none'};root_workflows={'present' if workflows.is_dir() else 'absent'}",
            category="ci",
        )
    )
    if hits:
        defects.append(Defect("CI-boundary defect", ".github/workflows", "no cursor jobs", ",".join(hits)))
    return checks, defects


def removed_reference_count() -> int:
    return len(REMOVED_ACTIVE_SURFACES)


def vscode_package_meta(monorepo: Path) -> tuple[str, str]:
    path = monorepo / "vscode-plugin" / "package.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return str(data.get("name") or ""), str(data.get("version") or "")


def check_vscode_static(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    name, version = vscode_package_meta(monorepo)
    checks.append(
        CheckResult(
            name="vscode:package_name",
            ok=name == EXPECTED_VSCODE_PACKAGE_NAME,
            detail=f"name={name}",
            category="vscode",
        )
    )
    checks.append(
        CheckResult(
            name="vscode:version_unchanged",
            ok=version == EXPECTED_VSCODE_VERSION,
            detail=f"version={version}",
            category="vscode",
        )
    )
    if version != EXPECTED_VSCODE_VERSION:
        defects.append(
            Defect(
                "VS Code regression",
                "package.json",
                EXPECTED_VSCODE_VERSION,
                version,
            )
        )
    return checks, defects
