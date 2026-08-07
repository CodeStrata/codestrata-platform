"""VS Code regression checks after Cursor removal."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from verification.cursor_extension_removal.contract import (
    EXPECTED_VSCODE_PACKAGE_NAME,
    EXPECTED_VSCODE_VERSION,
)
from verification.cursor_extension_removal.models import CheckResult, Defect

# Snapshot of VS Code command IDs that must remain after Slice 12.1.
REQUIRED_VSCODE_COMMANDS: frozenset[str] = frozenset(
    {
        "codestrata.assess",
        "codestrata.assessWithAi",
        "codestrata.installEngine",
        "codestrata.showWelcome",
        "codestrata.checkEnvironment",
        "codestrata.init",
        "codestrata.openHtmlReport",
        "codestrata.refreshFindings",
        "codestrata.refreshRecommendations",
        "codestrata.showRecommendations",
        "codestrata.clearResults",
        "codestrata.openOutput",
        "codestrata.openDocumentation",
        "codestrata.doctor",
    }
)


def _load_package(monorepo: Path) -> dict:
    path = monorepo / "vscode-plugin" / "package.json"
    return json.loads(path.read_text(encoding="utf-8"))


def check_vscode_static(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    root = monorepo / "vscode-plugin"
    present = root.is_dir()
    checks.append(
        CheckResult(
            name="vscode:directory_present",
            ok=present,
            detail=f"present={present}",
            category="vscode",
        )
    )
    if not present:
        defects.append(Defect("VS Code regression", "vscode-plugin", "present", "absent"))
        return checks, defects

    pkg = _load_package(monorepo)
    name = str(pkg.get("name") or "")
    version = str(pkg.get("version") or "")
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
            name="vscode:package_version_unchanged",
            ok=version == EXPECTED_VSCODE_VERSION,
            detail=f"version={version}",
            category="vscode",
        )
    )
    if version != EXPECTED_VSCODE_VERSION:
        defects.append(
            Defect(
                "VS Code regression",
                "vscode-plugin/package.json",
                EXPECTED_VSCODE_VERSION,
                version,
            )
        )

    commands = {
        str(item.get("command"))
        for item in (pkg.get("contributes") or {}).get("commands") or []
        if isinstance(item, dict)
    }
    missing = sorted(REQUIRED_VSCODE_COMMANDS - commands)
    checks.append(
        CheckResult(
            name="vscode:required_commands_intact",
            ok=not missing,
            detail=f"missing={missing or 'none'}",
            category="vscode",
        )
    )
    if missing:
        defects.append(
            Defect("VS Code regression", "commands", "required set intact", ",".join(missing))
        )

    src_hits = []
    src = root / "src"
    if src.is_dir():
        for path in src.rglob("*.ts"):
            text = path.read_text(encoding="utf-8", errors="ignore")
            if "from 'cursor-plugin" in text or 'from "cursor-plugin' in text:
                src_hits.append(path.name)
    checks.append(
        CheckResult(
            name="vscode:no_cursor_product_imports",
            ok=not src_hits,
            detail=f"hits={src_hits or 'none'}",
            category="vscode",
        )
    )
    if src_hits:
        defects.append(
            Defect("VS Code regression", "imports", "no cursor-plugin imports", ",".join(src_hits))
        )

    for rel in ("src/telemetry", "src/telemetry/analytics", "src/extension.ts"):
        ok = (root / rel).exists()
        checks.append(
            CheckResult(
                name=f"vscode:{rel.replace('/', '_')}_present",
                ok=ok,
                detail=f"present={ok}",
                category="vscode",
            )
        )
        if not ok:
            defects.append(Defect("VS Code regression", rel, "present", "absent"))

    return checks, defects


def run_vscode_compile(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    plugin = monorepo / "vscode-plugin"
    completed = subprocess.run(
        ["npm", "run", "compile"],
        cwd=str(plugin),
        capture_output=True,
        text=True,
        check=False,
    )
    ok = completed.returncode == 0
    checks.append(
        CheckResult(
            name="vscode:typescript_compile",
            ok=ok,
            detail=f"exit={completed.returncode}",
            category="vscode",
        )
    )
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
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    plugin = monorepo / "vscode-plugin"
    completed = subprocess.run(
        ["npm", "test"],
        cwd=str(plugin),
        capture_output=True,
        text=True,
        check=False,
    )
    ok = completed.returncode == 0
    checks.append(
        CheckResult(
            name="vscode:npm_test",
            ok=ok,
            detail=f"exit={completed.returncode}",
            category="vscode",
        )
    )
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


def check_vscode_regression(
    monorepo: Path,
    *,
    run_compile: bool = True,
    run_tests: bool = True,
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
    return checks, defects
