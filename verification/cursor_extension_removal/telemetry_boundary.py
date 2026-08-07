"""Telemetry boundary: Cursor emitter gone; historical vocabulary may remain."""

from __future__ import annotations

from pathlib import Path

from verification.cursor_extension_removal.contract import HISTORICAL_CURSOR_CLIENT_IDS
from verification.cursor_extension_removal.models import CheckResult, Defect


def check_telemetry_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    cursor_tel = monorepo / "cursor-plugin" / "src" / "telemetry"
    checks.append(
        CheckResult(
            name="telemetry:cursor_runtime_absent",
            ok=not cursor_tel.exists(),
            detail=f"absent={not cursor_tel.exists()}",
            category="telemetry",
        )
    )
    if cursor_tel.exists():
        defects.append(
            Defect(
                "telemetry compatibility defect",
                "cursor-plugin/src/telemetry",
                "absent",
                "present",
            )
        )

    vscode_tel = monorepo / "vscode-plugin" / "src" / "telemetry"
    checks.append(
        CheckResult(
            name="telemetry:vscode_runtime_present",
            ok=vscode_tel.is_dir(),
            detail=f"present={vscode_tel.is_dir()}",
            category="telemetry",
        )
    )

    # Historical vocabulary may still appear in Engine/Platform contracts.
    retained: list[str] = []
    search_roots = (
        monorepo / "engine" / "src",
        monorepo / "platform" / "src",
    )
    for root in search_roots:
        if not root.is_dir():
            continue
        for path in root.rglob("*.py"):
            text = path.read_text(encoding="utf-8", errors="ignore")
            for client_id in HISTORICAL_CURSOR_CLIENT_IDS:
                if client_id in text:
                    retained.append(f"{path.relative_to(monorepo)}:{client_id}")
                    break
    checks.append(
        CheckResult(
            name="telemetry:historical_cursor_vocabulary_may_remain",
            ok=True,
            detail=f"retained_refs={len(retained)} (historical deserialize only; Slice 12.4)",
            category="telemetry",
        )
    )
    return checks, defects
