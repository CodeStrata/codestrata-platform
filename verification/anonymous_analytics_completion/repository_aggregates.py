"""Repository aggregate analytics contract presence (Slice 10.5) — completion checks."""

from __future__ import annotations

from pathlib import Path

from verification.anonymous_analytics_completion.inventory import (
    EngineAnalyticsInventory,
    adapt_checks,
)
from verification.anonymous_analytics_completion.models import CheckResult, Defect
from verification.anonymous_analytics_privacy.runtime import (
    check_repository_aggregates as _check_repository_aggregates_108,
)

_REQUIRED_MODULES: tuple[str, ...] = (
    "repository_aggregate.py",
    "repository_aggregate_policy.py",
    "repository_aggregate_models.py",
    "repository_aggregate_input.py",
    "repository_aggregate_extractor.py",
    "repository_aggregate_validation.py",
    "repository_aggregate_projection.py",
    "repository_aggregate_serialization.py",
    "repository_aggregate_diagnostics.py",
    "repository_aggregate_compatibility.py",
)


def check_repository_aggregates(
    monorepo: Path,
    engine: EngineAnalyticsInventory,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    root = monorepo / "engine" / "src" / "codestrata" / "telemetry" / "analytics"

    for name in _REQUIRED_MODULES:
        ok = (root / name).is_file()
        checks.append(
            CheckResult(
                f"repository_aggregates:module_present:{name}",
                ok=ok,
                category="repository_aggregates",
            )
        )
        if not ok:
            defects.append(
                Defect("repository aggregate defect", name, "present", "missing")
            )

    raw_checks, raw_defects = _check_repository_aggregates_108(engine)
    adapted_checks, adapted_defects = adapt_checks(raw_checks, raw_defects)
    checks.extend(adapted_checks)
    defects.extend(adapted_defects)
    return checks, defects
