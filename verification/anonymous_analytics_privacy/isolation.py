"""Primary-operation isolation checks (Slice 10.8)."""

from __future__ import annotations

from pathlib import Path

from verification.anonymous_analytics_privacy.models import CheckResult, Defect
from verification.anonymous_analytics_privacy.vscode_inputs import VsCodeAnalyticsInventory


def check_isolation(
    vscode: VsCodeAnalyticsInventory,
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    isolation_ts = (
        monorepo / "vscode-plugin" / "src" / "telemetry" / "isolation.ts"
    ).read_text(encoding="utf-8")
    checks.append(
        CheckResult(
            name="isolation:vscode_fail_silent_analytics",
            ok=(
                "recordAnalyticsInvoked" in isolation_ts
                and "fail-silent" in isolation_ts.lower()
            ),
            category="isolation",
            contract="vscode",
        )
    )
    checks.append(
        CheckResult(
            name="isolation:vscode_rethrows_primary_error",
            ok="throw error" in isolation_ts,
            category="isolation",
            contract="vscode",
        )
    )
    checks.append(
        CheckResult(
            name="isolation:vscode_source_has_try_catch_around_analytics",
            ok="recordAnalyticsCompleted" in isolation_ts
            and isolation_ts.count("catch") >= 2,
            category="isolation",
            contract="vscode",
        )
    )

    # Engine construction APIs document fail-silent optional integration.
    engine_ai_policy = (
        monorepo
        / "engine"
        / "src"
        / "codestrata"
        / "telemetry"
        / "analytics"
        / "ai_analytics_policy.py"
    ).read_text(encoding="utf-8")
    checks.append(
        CheckResult(
            name="isolation:engine_fail_silent_optional",
            ok="fail_silent_optional_integration" in engine_ai_policy,
            category="isolation",
            contract="engine",
        )
    )

    for item in checks:
        if not item.ok:
            defects.append(Defect("isolation defect", item.name, "pass", "fail"))
    return checks, defects
