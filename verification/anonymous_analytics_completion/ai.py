"""AI analytics contract presence + OpenRouter/Epic 11 absence (Slice 10.6, completion)."""

from __future__ import annotations

from pathlib import Path

from verification.anonymous_analytics_completion.inventory import (
    EngineAnalyticsInventory,
    adapt_checks,
)
from verification.anonymous_analytics_completion.models import CheckResult, Defect
from verification.anonymous_analytics_privacy.runtime import check_ai as _check_ai_108

_REQUIRED_MODULES: tuple[str, ...] = (
    "ai_analytics.py",
    "ai_analytics_policy.py",
    "ai_analytics_catalogs.py",
    "ai_analytics_input.py",
    "ai_analytics_mapping.py",
    "ai_analytics_models.py",
    "ai_analytics_projection.py",
    "ai_analytics_validation.py",
    "ai_analytics_serialization.py",
    "ai_analytics_diagnostics.py",
    "ai_analytics_compatibility.py",
)


def check_ai(
    monorepo: Path,
    engine: EngineAnalyticsInventory,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    root = monorepo / "engine" / "src" / "codestrata" / "telemetry" / "analytics"

    for name in _REQUIRED_MODULES:
        ok = (root / name).is_file()
        checks.append(
            CheckResult(f"ai:module_present:{name}", ok=ok, category="ai")
        )
        if not ok:
            defects.append(Defect("AI analytics defect", name, "present", "missing"))

    raw_checks, raw_defects = _check_ai_108(engine)
    adapted_checks, adapted_defects = adapt_checks(raw_checks, raw_defects)
    checks.extend(adapted_checks)
    defects.extend(adapted_defects)

    ok_no_openrouter = "openrouter" not in engine.ai_provider_families
    checks.append(
        CheckResult(
            "ai:openrouter_absent_from_provider_families",
            ok=ok_no_openrouter,
            detail=",".join(sorted(engine.ai_provider_families)),
            category="ai",
        )
    )
    if not ok_no_openrouter:
        defects.append(
            Defect(
                "boundary defect",
                "ai_provider_families",
                "openrouter absent",
                "openrouter present",
            )
        )
    return checks, defects
