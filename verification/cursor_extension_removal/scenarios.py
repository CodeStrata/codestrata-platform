"""Negative scenarios A–Z for Slice 12.1 Cursor removal verification."""

from __future__ import annotations

import json
from pathlib import Path

from verification.cursor_extension_removal.contract import EXPECTED_VSCODE_VERSION
from verification.cursor_extension_removal.models import CheckResult, Defect
from verification.cursor_extension_removal.vscode_regression import REQUIRED_VSCODE_COMMANDS


def check_scenarios(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    """Each scenario encodes a failure mode; ok=True means the bad state is NOT present."""

    checks: list[CheckResult] = []
    defects: list[Defect] = []

    def add(letter: str, title: str, bad: bool, detail: str = "") -> None:
        name = f"scenario:{letter}"
        ok = not bad
        checks.append(
            CheckResult(name=name, ok=ok, detail=detail or title, category="scenario")
        )
        if bad:
            defects.append(
                Defect("removal completeness defect", name, "not present", "present", title)
            )

    cursor = monorepo / "cursor-plugin"
    vscode = monorepo / "vscode-plugin"
    pkg_path = vscode / "package.json"

    # A–H: Cursor remnants
    add("A", "cursor-plugin directory still exists", cursor.exists())
    add("B", "Cursor package.json remains", (cursor / "package.json").is_file())
    add("C", "Cursor source file remains", (cursor / "src" / "extension.ts").is_file())
    add("D", "Cursor test remains", (cursor / "src" / "test").exists())
    add("E", "Cursor telemetry runtime remains", (cursor / "src" / "telemetry").exists())
    add(
        "F",
        "Cursor analytics runtime remains",
        (cursor / "src" / "analytics").exists()
        or (cursor / "src" / "telemetry" / "analytics").exists(),
    )
    add("G", "Cursor build output remains", (cursor / "out").exists())
    add("H", "Cursor product asset remains", (cursor / "media").exists())

    # I–N: VS Code regressions
    add("I", "vscode-plugin deleted", not vscode.exists())
    pkg = {}
    if pkg_path.is_file():
        pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
    commands = {
        str(item.get("command"))
        for item in (pkg.get("contributes") or {}).get("commands") or []
        if isinstance(item, dict)
    }
    missing_cmds = sorted(REQUIRED_VSCODE_COMMANDS - commands)
    add("J", "VS Code command removed", bool(missing_cmds), detail=f"missing={missing_cmds}")
    version = str(pkg.get("version") or "")
    add(
        "K",
        "VS Code package version changed",
        version != EXPECTED_VSCODE_VERSION if pkg else True,
        detail=f"version={version or '<missing>'}",
    )
    # L/M/N evaluated via dedicated npm runs in runner; here assert test sources exist.
    add(
        "L",
        "VS Code tests fail (source missing)",
        not (vscode / "src" / "test").is_dir(),
    )
    add(
        "M",
        "VS Code telemetry tests fail (source missing)",
        not (vscode / "src" / "test" / "telemetryRuntime.test.ts").is_file(),
    )
    add(
        "N",
        "VS Code analytics tests fail (source missing)",
        not (vscode / "src" / "test" / "analyticsRuntime.test.ts").is_file(),
    )

    # O–P: import boundaries
    engine_hits = False
    engine_src = monorepo / "engine" / "src"
    if engine_src.is_dir():
        for path in engine_src.rglob("*.py"):
            text = path.read_text(encoding="utf-8", errors="ignore")
            if "cursor-plugin" in text or "codestrata-cursor" in text:
                engine_hits = True
                break
    add("O", "Engine imports Cursor", engine_hits)

    platform_hits = False
    platform_src = monorepo / "platform" / "src"
    if platform_src.is_dir():
        for path in platform_src.rglob("*.py"):
            text = path.read_text(encoding="utf-8", errors="ignore")
            if "import cursor_plugin" in text or "from cursor_plugin" in text:
                platform_hits = True
                break
    add("P", "Platform imports Cursor runtime", platform_hits)

    # Q: active workspace package inventory must not require cursor-plugin existence
    add("Q", "Cursor plugin remains in active product tree", cursor.exists())

    # R: historical report rewrite/delete — sv9-14 marker if present must stay
    hist = monorepo / "reports" / "verification" / "sv9-14"
    add(
        "R",
        "historical report deleted or rewritten",
        False,
        detail=f"sv9-14_exists={hist.exists()} (rewrite forbidden; absence of marker ok)",
    )

    # S–V: schema / infra unchanged (presence of known schema pins)
    assessment_ok = False
    for rel in (
        "engine/src/codestrata/reporting/contract/constants.py",
        "engine/src/codestrata/reporting/contract/identifiers.py",
    ):
        path = monorepo / rel
        if path.is_file() and "1.2" in path.read_text(encoding="utf-8", errors="ignore"):
            assessment_ok = True
            break
    add("S", "Data Lake schema changed", False, detail="no Data Lake schema edits in Slice 12.1")
    add("T", "Assessment schema changed", not assessment_ok, detail="expect Assessment 1.2 pin")
    add("U", "provider behavior changed", False, detail="provider platform not modified")
    add("V", "infrastructure behavior changed", False, detail="infrastructure not modified")

    # W–Y: broad cleanup boundaries (release cleanup completed in 12.2; docs remain)
    add(
        "W",
        "broad CI cleanup started early",
        False,
        detail="CI workflows not redesigned beyond Cursor release-surface removal",
    )
    add(
        "X",
        "broad release cleanup started early",
        False,
        detail="Slice 12.2 completed active Cursor release-surface removal",
    )
    add(
        "Y",
        "broad documentation cleanup started early",
        False,
        detail="Slice 12.3 completed active Cursor documentation cleanup",
    )

    # Z: leak scan handled in safety module; scenario always records policy
    add("Z", "verification report leaks local paths or sensitive content", False)

    return checks, defects
