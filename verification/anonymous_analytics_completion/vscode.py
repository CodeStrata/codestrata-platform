"""VS Code analytics contract presence (Slice 10.7) — completion checks."""

from __future__ import annotations

from pathlib import Path

from verification.anonymous_analytics_completion.inventory import (
    VsCodeAnalyticsInventory,
    adapt_checks,
)
from verification.anonymous_analytics_completion.models import CheckResult, Defect
from verification.anonymous_analytics_privacy.runtime import (
    check_vscode as _check_vscode_108,
)

_REQUIRED_MODULES: tuple[str, ...] = (
    "runtimePolicy.ts",
    "schema.ts",
    "events.ts",
    "consent.ts",
    "projection.ts",
    "validation.ts",
    "serialization.ts",
    "diagnostics.ts",
    "isolation.ts",
    "sink.ts",
    "unavailableSink.ts",
    "captureSink.ts",
    "catalogMapping.ts",
    "compatibility.ts",
    "preview.ts",
    "errors.ts",
    "index.ts",
)


def check_vscode(
    monorepo: Path,
    vscode: VsCodeAnalyticsInventory,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    root = monorepo / "vscode-plugin" / "src" / "telemetry" / "analytics"

    for name in _REQUIRED_MODULES:
        ok = (root / name).is_file()
        checks.append(
            CheckResult(f"vscode:module_present:{name}", ok=ok, category="vscode")
        )
        if not ok:
            defects.append(Defect("VS Code analytics defect", name, "present", "missing"))

    raw_checks, raw_defects = _check_vscode_108(vscode)
    adapted_checks, adapted_defects = adapt_checks(raw_checks, raw_defects)
    checks.extend(adapted_checks)
    defects.extend(adapted_defects)
    return checks, defects
