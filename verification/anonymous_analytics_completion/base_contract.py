"""Base anonymous analytics contract presence (Slice 10.1) — completion checks."""

from __future__ import annotations

from pathlib import Path

from codestrata.telemetry.analytics.events import (
    FORBIDDEN_ANALYTICS_FIELD_NAMES,
    AnalyticsCategory,
)
from codestrata.telemetry.analytics.policy import default_analytics_policy
from verification.anonymous_analytics_completion.models import CheckResult, Defect

_REQUIRED_MODULES: tuple[str, ...] = (
    "policy.py",
    "events.py",
    "projection.py",
    "validation.py",
    "serialization.py",
    "diagnostics.py",
    "errors.py",
    "compatibility.py",
)

_REQUIRED_CATEGORIES = {
    "runtime",
    "assessment",
    "repository_aggregates",
    "ai_usage",
    "vscode_usage",
}


def check_base_contract(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    root = monorepo / "engine" / "src" / "codestrata" / "telemetry" / "analytics"

    for name in _REQUIRED_MODULES:
        ok = (root / name).is_file()
        checks.append(
            CheckResult(f"base:module_present:{name}", ok=ok, category="base")
        )
        if not ok:
            defects.append(Defect("base-contract defect", name, "present", "missing"))

    policy = default_analytics_policy()
    checks.append(
        CheckResult(
            "base:collection_disabled",
            ok=not policy.collection_enabled,
            category="base",
        )
    )
    checks.append(
        CheckResult(
            "base:persistence_disabled",
            ok=not policy.persistence_enabled,
            category="base",
        )
    )
    checks.append(
        CheckResult(
            "base:transmission_disabled",
            ok=not policy.transmission_enabled,
            category="base",
        )
    )
    checks.append(
        CheckResult(
            "base:installation_id_forbidden",
            ok="installation_id" in FORBIDDEN_ANALYTICS_FIELD_NAMES
            and not policy.installation_id_allowed,
            category="base",
        )
    )
    checks.append(
        CheckResult(
            "base:categories_closed_vocabulary",
            ok=_REQUIRED_CATEGORIES <= {c.value for c in AnalyticsCategory},
            category="base",
        )
    )

    _defect_prefixes = (
        "base:collection",
        "base:persistence",
        "base:transmission",
        "base:installation",
        "base:categories",
    )
    for item in checks:
        if not item.ok and item.name.startswith(_defect_prefixes):
            defects.append(Defect("base-contract defect", item.name, "pass", "fail"))
    return checks, defects
