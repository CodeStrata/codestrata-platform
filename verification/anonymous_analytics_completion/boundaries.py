"""Platform / Data Lake / Cursor boundary checks and Epic 11 absence (Slice 10.9).

Reuses Slice 10.8's ``check_boundaries`` and adds a dedicated Epic 11 / AI
Provider Platform / OpenRouter absence scan scoped to Engine, Platform, and
VS Code product source trees (documentation mentioning future work is
allowed).
"""

from __future__ import annotations

from pathlib import Path

from verification.anonymous_analytics_completion.inventory import (
    VsCodeAnalyticsInventory,
    adapt_checks,
)
from verification.anonymous_analytics_completion.models import CheckResult, Defect
from verification.anonymous_analytics_privacy.boundaries import (
    check_boundaries as _check_boundaries_108,
)

_EPIC11_FORBIDDEN_DIR_NAMES: frozenset[str] = frozenset(
    {
        "openrouter",
        "ai_provider_platform",
        "provider_platform",
        "provider_registry",
        "capability_discovery",
    }
)

_PRODUCT_SEARCH_ROOTS: tuple[str, ...] = (
    "engine/src",
    "engine/platform",
    "platform/src",
    "vscode-plugin/src",
)


def check_boundaries(
    monorepo: Path,
    vscode: VsCodeAnalyticsInventory,
) -> tuple[list[CheckResult], list[Defect], dict[str, str]]:
    raw_checks, raw_defects = _check_boundaries_108(monorepo, vscode)
    checks, defects = adapt_checks(raw_checks, raw_defects)

    dashboard_hits: list[str] = []
    for root_rel in ("platform/src", "engine/src"):
        root = monorepo / root_rel
        if root.is_dir():
            dashboard_hits.extend(
                str(p.relative_to(monorepo)) for p in root.rglob("*analytics_dashboard*")
            )
    checks.append(
        CheckResult(
            "boundary:no_analytics_dashboard",
            ok=not dashboard_hits,
            detail=",".join(dashboard_hits[:5]),
            category="boundary",
        )
    )
    if dashboard_hits:
        defects.append(
            Defect("boundary defect", "analytics_dashboard", "absent", ",".join(dashboard_hits[:5]))
        )

    cursor_analytics_hits: list[str] = []
    cursor_root = monorepo / "cursor-plugin" / "src"
    if cursor_root.is_dir():
        for path in cursor_root.rglob("*"):
            if path.is_file() and "analytics" in path.name.lower():
                cursor_analytics_hits.append(path.name)
    checks.append(
        CheckResult(
            "boundary:no_cursor_analytics_runtime",
            ok=not cursor_analytics_hits,
            detail=",".join(cursor_analytics_hits),
            category="boundary",
        )
    )
    if cursor_analytics_hits:
        defects.append(
            Defect(
                "boundary defect", "cursor_analytics", "absent", ",".join(cursor_analytics_hits)
            )
        )

    data_lake_hits: list[str] = []
    analytics_root = monorepo / "engine" / "src" / "codestrata" / "telemetry" / "analytics"
    if analytics_root.is_dir():
        for path in analytics_root.rglob("*.py"):
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                stripped = line.strip()
                if stripped.startswith(("import ", "from ")) and (
                    "data_lake" in stripped or "community_data_lake" in stripped
                ):
                    data_lake_hits.append(path.name)
                    break
    checks.append(
        CheckResult(
            "boundary:engine_analytics_no_data_lake_imports",
            ok=not data_lake_hits,
            detail=",".join(data_lake_hits[:5]),
            category="boundary",
        )
    )
    if data_lake_hits:
        defects.append(
            Defect("boundary defect", "data_lake_imports", "absent", ",".join(data_lake_hits[:5]))
        )

    platform_names = (
        "boundary:engine_no_platform_datalake_imports",
        "boundary:no_platform_anonymous_analytics_processor",
    )
    data_lake_names = (
        "boundary:engine_no_platform_datalake_imports",
        "boundary:engine_analytics_no_data_lake_imports",
    )
    cursor_names = (
        "boundary:cursor_no_analytics_runtime",
        "boundary:no_cursor_analytics_runtime",
    )
    statuses = {
        "platform_boundary_status": (
            "pass" if all(c.ok for c in checks if c.name in platform_names) else "fail"
        ),
        "data_lake_boundary_status": (
            "pass" if all(c.ok for c in checks if c.name in data_lake_names) else "fail"
        ),
        "cursor_boundary_status": (
            "pass" if all(c.ok for c in checks if c.name in cursor_names) else "fail"
        ),
    }
    return checks, defects, statuses


def check_epic11_absence(monorepo: Path) -> tuple[str, list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    hits: list[str] = []

    for root_rel in _PRODUCT_SEARCH_ROOTS:
        root = monorepo / root_rel
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if path.is_dir() and path.name.lower() in _EPIC11_FORBIDDEN_DIR_NAMES:
                hits.append(str(path.relative_to(monorepo)))

    checks.append(
        CheckResult(
            "epic11:packages_absent",
            ok=not hits,
            detail=",".join(sorted(hits)[:5]) if hits else "absent",
            category="epic11",
        )
    )
    if hits:
        defects.append(
            Defect("boundary defect", "epic11_packages", "absent", ",".join(sorted(hits)[:5]))
        )

    ai_policy = (
        monorepo
        / "engine" / "src" / "codestrata" / "telemetry" / "analytics" / "ai_analytics_catalogs.py"
    )
    ai_text = ai_policy.read_text(encoding="utf-8") if ai_policy.is_file() else ""
    checks.append(
        CheckResult(
            "epic11:openrouter_not_in_approved_provider_families",
            ok="openrouter" not in ai_text.lower(),
            category="epic11",
        )
    )
    if "openrouter" in ai_text.lower():
        defects.append(
            Defect(
                "boundary defect",
                "ai_analytics_catalogs",
                "no openrouter",
                "openrouter present",
            )
        )

    status = "pass" if all(c.ok for c in checks) else "fail"
    return status, checks, defects
