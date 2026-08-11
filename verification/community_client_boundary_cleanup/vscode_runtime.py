"""VS Code runtime regression checks (Slice 12.4)."""

from __future__ import annotations

import json
from pathlib import Path

from verification.community_client_boundary_cleanup.contract import EXPECTED_VSCODE_VERSION
from verification.community_client_boundary_cleanup.models import CheckResult, Defect


def check_vscode_runtime(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    vscode = monorepo / "vscode-plugin"
    pkg_path = vscode / "package.json"
    cursor_dir = monorepo / "cursor-plugin"

    checks.append(
        CheckResult(
            "vscode:package_present",
            ok=pkg_path.is_file(),
            detail="vscode-plugin/package.json",
            category="vscode",
        )
    )
    checks.append(
        CheckResult(
            "vscode:cursor_runtime_absent",
            ok=not cursor_dir.exists(),
            detail="cursor-plugin/ absent",
            category="vscode",
        )
    )

    if pkg_path.is_file():
        pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
        version_ok = str(pkg.get("version")) == EXPECTED_VSCODE_VERSION
        name_ok = str(pkg.get("name")) == "codestrata-assessment"
        checks.append(
            CheckResult(
                "vscode:version_unchanged",
                ok=version_ok,
                detail=f"version={pkg.get('version')}",
                category="vscode",
            )
        )
        checks.append(
            CheckResult(
                "vscode:package_name_unchanged",
                ok=name_ok,
                detail=f"name={pkg.get('name')}",
                category="vscode",
            )
        )
        if not version_ok or not name_ok:
            defects.append(
                Defect(
                    "VS Code regression",
                    "vscode-plugin/package.json",
                    f"codestrata-assessment@{EXPECTED_VSCODE_VERSION}",
                    f"{pkg.get('name')}@{pkg.get('version')}",
                )
            )

    # No Cursor client selection in VS Code sources.
    cursor_hits = 0
    src = vscode / "src"
    if src.is_dir():
        for path in src.rglob("*.ts"):
            text = path.read_text(encoding="utf-8", errors="ignore")
            if "cursor_extension" in text or "CursorExtension" in text:
                cursor_hits += 1
    checks.append(
        CheckResult(
            "vscode:no_cursor_client_construction",
            ok=cursor_hits == 0,
            detail=f"src_hits={cursor_hits}",
            category="vscode",
        )
    )
    if cursor_hits:
        defects.append(
            Defect(
                "VS Code regression",
                "vscode-plugin/src",
                "no cursor_extension",
                f"hits={cursor_hits}",
            )
        )
    return checks, defects
