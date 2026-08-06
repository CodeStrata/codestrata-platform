"""Runtime analytics contract presence and unwiring (Slice 10.3) — completion checks.

Reuses Slice 10.8's ``check_runtime`` and ``check_product_paths`` directly per
the Slice 10.9 brief instead of re-implementing runtime-analytics behavior.
"""

from __future__ import annotations

from pathlib import Path

from verification.anonymous_analytics_completion.inventory import (
    EngineAnalyticsInventory,
    adapt_checks,
)
from verification.anonymous_analytics_completion.models import CheckResult, Defect
from verification.anonymous_analytics_privacy.runtime import (
    check_product_paths as _check_product_paths_108,
)
from verification.anonymous_analytics_privacy.runtime import (
    check_runtime as _check_runtime_108,
)

_REQUIRED_MODULES: tuple[str, ...] = (
    "runtime_analytics.py",
    "runtime_analytics_projection.py",
    "runtime_analytics_validation.py",
    "runtime_analytics_serialization.py",
    "runtime_analytics_diagnostics.py",
    "runtime_analytics_compatibility.py",
)


def check_runtime_analytics(
    monorepo: Path,
    engine: EngineAnalyticsInventory,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    root = monorepo / "engine" / "src" / "codestrata" / "telemetry" / "analytics"

    for name in _REQUIRED_MODULES:
        ok = (root / name).is_file()
        checks.append(
            CheckResult(f"runtime:module_present:{name}", ok=ok, category="runtime")
        )
        if not ok:
            defects.append(Defect("runtime analytics defect", name, "present", "missing"))

    raw_checks, raw_defects = _check_runtime_108(engine)
    adapted_checks, adapted_defects = adapt_checks(raw_checks, raw_defects)
    checks.extend(adapted_checks)
    defects.extend(adapted_defects)
    return checks, defects


def check_product_paths(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    raw_checks, raw_defects = _check_product_paths_108(monorepo)
    return adapt_checks(raw_checks, raw_defects)
