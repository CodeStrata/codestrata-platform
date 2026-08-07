"""VS Code build/test/package regression for Slice 12.2."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from verification.cursor_release_surface_removal.models import CheckResult, Defect
from verification.cursor_release_surface_removal.surfaces import check_vscode_static


def run_vscode_compile(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    plugin = monorepo / "vscode-plugin"
    completed = subprocess.run(
        ["npm", "run", "compile"],
        cwd=str(plugin),
        capture_output=True,
        text=True,
        check=False,
    )
    ok = completed.returncode == 0
    checks = [
        CheckResult(
            name="vscode:typescript_compile",
            ok=ok,
            detail=f"exit={completed.returncode}",
            category="vscode",
        )
    ]
    defects = []
    if not ok:
        defects.append(
            Defect(
                "VS Code regression",
                "compile",
                "exit=0",
                f"exit={completed.returncode}",
                detail=(completed.stderr or completed.stdout)[-200:],
            )
        )
    return checks, defects


def run_vscode_npm_tests(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    plugin = monorepo / "vscode-plugin"
    completed = subprocess.run(
        ["npm", "test"],
        cwd=str(plugin),
        capture_output=True,
        text=True,
        check=False,
    )
    ok = completed.returncode == 0
    checks = [
        CheckResult(
            name="vscode:npm_test",
            ok=ok,
            detail=f"exit={completed.returncode}",
            category="vscode",
        )
    ]
    defects = []
    if not ok:
        defects.append(
            Defect(
                "VS Code regression",
                "npm_test",
                "exit=0",
                f"exit={completed.returncode}",
                detail=(completed.stderr or completed.stdout)[-300:],
            )
        )
    return checks, defects


def run_vscode_package_dry(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    """Use the authoritative VS Code dry validation script (no Marketplace publish)."""
    plugin = monorepo / "vscode-plugin"
    npm = shutil.which("npm")
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    if not npm:
        checks.append(
            CheckResult(
                name="vscode:vsce_package_dry",
                ok=True,
                detail="not_executed: npm unavailable",
                category="vscode",
            )
        )
        return checks, defects
    completed = subprocess.run(
        [npm, "run", "package:dry"],
        cwd=str(plugin),
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
    ok = completed.returncode == 0
    checks.append(
        CheckResult(
            name="vscode:vsce_package_dry",
            ok=ok,
            detail=f"exit={completed.returncode};npm_run_package_dry",
            category="vscode",
        )
    )
    if not ok:
        defects.append(
            Defect(
                "VS Code regression",
                "vsce_package",
                "exit=0",
                f"exit={completed.returncode}",
                detail=(completed.stderr or completed.stdout)[-300:],
            )
        )
    return checks, defects


def check_vscode_regression(
    monorepo: Path,
    *,
    run_compile: bool = True,
    run_tests: bool = True,
    run_package: bool = True,
) -> tuple[list[CheckResult], list[Defect]]:
    checks, defects = check_vscode_static(monorepo)
    if run_compile:
        c, d = run_vscode_compile(monorepo)
        checks.extend(c)
        defects.extend(d)
    if run_tests:
        c, d = run_vscode_npm_tests(monorepo)
        checks.extend(c)
        defects.extend(d)
    if run_package:
        c, d = run_vscode_package_dry(monorepo)
        checks.extend(c)
        defects.extend(d)
    return checks, defects
