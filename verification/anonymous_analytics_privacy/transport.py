"""Transport / sink boundary checks (Slice 10.8)."""

from __future__ import annotations

from pathlib import Path

from verification.anonymous_analytics_privacy.engine_inputs import EngineAnalyticsInventory
from verification.anonymous_analytics_privacy.models import CheckResult, Defect
from verification.anonymous_analytics_privacy.vscode_inputs import VsCodeAnalyticsInventory


def check_transport(
    engine: EngineAnalyticsInventory,
    vscode: VsCodeAnalyticsInventory,
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    checks.append(
        CheckResult(
            name="transport:engine_base_transmission_disabled",
            ok=not engine.base_transmission_enabled,
            category="transport",
            contract="base",
        )
    )
    checks.append(
        CheckResult(
            name="transport:engine_slice_transmission_disabled",
            ok=(
                not engine.runtime_transmission_enabled
                and not engine.assessment_transmission_enabled
                and not engine.repository_transmission_enabled
                and not engine.ai_transmission_enabled
            ),
            category="transport",
            contract="engine",
        )
    )
    checks.append(
        CheckResult(
            name="transport:vscode_unavailable_sink",
            ok="UnavailableVsCodeAnalyticsSink" in vscode.source_blob
            and "defaultUnavailableAnalyticsSink" in vscode.source_blob,
            category="transport",
            contract="vscode",
        )
    )
    checks.append(
        CheckResult(
            name="transport:vscode_no_http",
            ok=not vscode.has_http_imports,
            category="transport",
            contract="vscode",
        )
    )

    analytics_root = monorepo / "engine" / "src" / "codestrata" / "telemetry" / "analytics"
    http_hits = []
    if analytics_root.is_dir():
        for path in analytics_root.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            for needle in ("urllib", "requests.", "http.client", "aiohttp", "boto3"):
                if needle in text:
                    http_hits.append(f"{path.name}:{needle}")
    checks.append(
        CheckResult(
            name="transport:engine_analytics_no_http_clients",
            ok=http_hits == [],
            detail=",".join(http_hits[:5]),
            category="transport",
            contract="engine",
        )
    )

    for item in checks:
        if not item.ok:
            defects.append(Defect("transport defect", item.name, "pass", "fail"))
    return checks, defects
