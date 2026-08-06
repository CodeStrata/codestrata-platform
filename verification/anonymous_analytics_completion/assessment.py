"""Assessment analytics contract presence (Slice 10.4) — completion checks."""

from __future__ import annotations

from pathlib import Path

from verification.anonymous_analytics_completion.inventory import (
    EngineAnalyticsInventory,
    adapt_checks,
)
from verification.anonymous_analytics_completion.models import CheckResult, Defect
from verification.anonymous_analytics_privacy.runtime import (
    check_assessment as _check_assessment_108,
)

_REQUIRED_MODULES: tuple[str, ...] = (
    "assessment_analytics.py",
    "assessment_analytics_policy.py",
    "assessment_analytics_validation.py",
    "assessment_analytics_diagnostics.py",
    "assessment_analytics_compatibility.py",
    "assessment_analytics_serialization.py",
    "assessment_analytics_projection.py",
)


def check_assessment(
    monorepo: Path,
    engine: EngineAnalyticsInventory,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    root = monorepo / "engine" / "src" / "codestrata" / "telemetry" / "analytics"

    for name in _REQUIRED_MODULES:
        ok = (root / name).is_file()
        checks.append(
            CheckResult(f"assessment:module_present:{name}", ok=ok, category="assessment")
        )
        if not ok:
            defects.append(Defect("assessment analytics defect", name, "present", "missing"))

    raw_checks, raw_defects = _check_assessment_108(engine)
    adapted_checks, adapted_defects = adapt_checks(raw_checks, raw_defects)
    checks.extend(adapted_checks)
    defects.extend(adapted_defects)
    return checks, defects
