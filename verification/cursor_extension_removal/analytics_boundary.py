"""Analytics boundary: Cursor analytics runtime gone; historical ids may remain."""

from __future__ import annotations

from pathlib import Path

from verification.cursor_extension_removal.models import CheckResult, Defect


def check_analytics_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    cursor_analytics_paths = (
        monorepo / "cursor-plugin" / "src" / "analytics",
        monorepo / "cursor-plugin" / "src" / "telemetry" / "analytics",
    )
    present = any(p.exists() for p in cursor_analytics_paths)
    checks.append(
        CheckResult(
            name="analytics:cursor_runtime_absent",
            ok=not present,
            detail=f"absent={not present}",
            category="analytics",
        )
    )
    if present:
        defects.append(
            Defect(
                "analytics compatibility defect",
                "cursor-plugin analytics runtime",
                "absent",
                "present",
            )
        )

    vscode_analytics = monorepo / "vscode-plugin" / "src" / "telemetry" / "analytics"
    checks.append(
        CheckResult(
            name="analytics:vscode_runtime_present",
            ok=vscode_analytics.is_dir(),
            detail=f"present={vscode_analytics.is_dir()}",
            category="analytics",
        )
    )
    return checks, defects
