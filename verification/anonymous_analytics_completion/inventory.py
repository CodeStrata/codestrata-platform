"""Live Engine/VS Code analytics inventories for completion verification (Slice 10.9).

Reuses the Slice 10.8 loaders directly instead of re-implementing Engine
policy imports or VS Code TypeScript source parsing.
"""

from __future__ import annotations

from verification.anonymous_analytics_completion.models import CheckResult, Defect
from verification.anonymous_analytics_privacy.engine_inputs import (
    EngineAnalyticsInventory,
    load_engine_inventory,
)
from verification.anonymous_analytics_privacy.vscode_inputs import (
    VsCodeAnalyticsInventory,
    load_vscode_analytics_inventory,
)


def adapt_checks(
    checks: list,
    defects: list,
) -> tuple[list[CheckResult], list[Defect]]:
    """Adapt Slice 10.8 CheckResult/Defect (with a ``contract`` field) to Slice 10.9 models."""

    adapted_checks = [
        CheckResult(name=c.name, ok=c.ok, detail=c.detail, category=c.category)
        for c in checks
    ]
    adapted_defects = [
        Defect(
            classification=d.classification,
            component=d.component,
            expected=d.expected,
            actual=d.actual,
            detail=d.detail,
        )
        for d in defects
    ]
    return adapted_checks, adapted_defects


__all__ = [
    "EngineAnalyticsInventory",
    "VsCodeAnalyticsInventory",
    "adapt_checks",
    "load_engine_inventory",
    "load_vscode_analytics_inventory",
]
