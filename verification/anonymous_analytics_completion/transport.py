"""Transport boundary checks (Slice 10.9 completion).

Reuses Slice 10.8's ``check_transport`` and adds an explicit structural check
that the Engine analytics package carries no transport module at all, and
that VS Code analytics remains the unavailable sink only.
"""

from __future__ import annotations

from pathlib import Path

from verification.anonymous_analytics_completion.inventory import (
    EngineAnalyticsInventory,
    VsCodeAnalyticsInventory,
    adapt_checks,
)
from verification.anonymous_analytics_completion.models import CheckResult, Defect
from verification.anonymous_analytics_privacy.transport import (
    check_transport as _check_transport_108,
)

_FORBIDDEN_ENGINE_TRANSPORT_FILES: tuple[str, ...] = (
    "transport.py",
    "transport_factory.py",
    "transport_http.py",
    "http_transport.py",
    "http_client.py",
)


def check_transport(
    monorepo: Path,
    engine: EngineAnalyticsInventory,
    vscode: VsCodeAnalyticsInventory,
) -> tuple[list[CheckResult], list[Defect]]:
    raw_checks, raw_defects = _check_transport_108(engine, vscode, monorepo)
    checks, defects = adapt_checks(raw_checks, raw_defects)

    analytics_root = monorepo / "engine" / "src" / "codestrata" / "telemetry" / "analytics"
    hits = [
        name for name in _FORBIDDEN_ENGINE_TRANSPORT_FILES if (analytics_root / name).is_file()
    ]
    checks.append(
        CheckResult(
            "transport:engine_analytics_no_transport_module",
            ok=not hits,
            detail=",".join(hits),
            category="transport",
        )
    )
    if hits:
        defects.append(
            Defect(
                "transport defect",
                "engine_analytics_transport_module",
                "absent",
                ",".join(hits),
            )
        )

    checks.append(
        CheckResult(
            "transport:vscode_only_unavailable_sink_implementation",
            ok="UnavailableVsCodeAnalyticsSink" in vscode.source_blob
            and not vscode.has_http_imports,
            category="transport",
        )
    )

    return checks, defects
