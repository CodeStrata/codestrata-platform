"""Persistence boundary checks (Slice 10.9 completion).

Reuses Slice 10.8's ``check_persistence`` and adds a check that only the
Slice 10.2 installation identity JSON file is ever written, with no
analytics event queue, retry, or batching persistence introduced.
"""

from __future__ import annotations

from pathlib import Path

from verification.anonymous_analytics_completion.inventory import (
    EngineAnalyticsInventory,
    VsCodeAnalyticsInventory,
    adapt_checks,
)
from verification.anonymous_analytics_completion.models import CheckResult, Defect
from verification.anonymous_analytics_privacy.persistence import (
    check_persistence as _check_persistence_108,
)

_QUEUE_RETRY_NEEDLES: tuple[str, ...] = (
    "event_queue",
    "EventQueue",
    "retry_queue",
    "RetryQueue",
    "sqlite3",
    ".jsonl",
    "batch_writer",
)


def check_persistence(
    monorepo: Path,
    engine: EngineAnalyticsInventory,
    vscode: VsCodeAnalyticsInventory,
    *,
    tmp_home: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    raw_checks, raw_defects = _check_persistence_108(engine, vscode, tmp_home=tmp_home)
    checks, defects = adapt_checks(raw_checks, raw_defects)

    analytics_root = monorepo / "engine" / "src" / "codestrata" / "telemetry" / "analytics"
    hits: list[str] = []
    for path in sorted(analytics_root.rglob("*.py")):
        text = path.read_text(encoding="utf-8", errors="replace")
        for needle in _QUEUE_RETRY_NEEDLES:
            if needle in text:
                hits.append(f"{path.name}:{needle}")
    checks.append(
        CheckResult(
            "persistence:no_analytics_event_queue_or_retry",
            ok=not hits,
            detail=",".join(sorted(set(hits))[:5]) if hits else "clean",
            category="persistence",
        )
    )
    if hits:
        defects.append(
            Defect(
                "persistence defect",
                "queue_retry_batching",
                "absent",
                ",".join(sorted(set(hits))[:5]),
            )
        )

    storage_module = analytics_root / "installation_identity_storage.py"
    storage_text = storage_module.read_text(encoding="utf-8") if storage_module.is_file() else ""
    checks.append(
        CheckResult(
            "persistence:only_identity_json_filename_referenced",
            ok="anonymous-installation-identity.json" not in storage_text
            and "IDENTITY_FILENAME" in storage_text,
            category="persistence",
        )
    )

    return checks, defects
