"""Export target consistency."""

from __future__ import annotations

import re
from pathlib import Path

from verification.repository_consistency.contract import EXPORT_TARGETS, FORBIDDEN_EXPORT_TARGETS
from verification.repository_consistency.inventory import add_check
from verification.repository_consistency.models import CheckResult, Defect


def check_exports(monorepo: Path) -> tuple[list[CheckResult], list[Defect], list[dict[str, str]]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    results: list[dict[str, str]] = []

    targets_py = monorepo / "scripts/repository_export_router/targets.py"
    add_check(checks, defects, "exports:router_targets_exist", targets_py.is_file(), str(targets_py.name), "exports")
    if targets_py.is_file():
        text = targets_py.read_text(encoding="utf-8")
        for t in EXPORT_TARGETS:
            ok = f'"{t}"' in text or f"'{t}'" in text or f"= \"{t}\"" in text or f"{t.upper()}" in text
            add_check(checks, defects, f"exports:target:{t}", ok, t, "exports")
            results.append({"target": t, "status": "present" if ok else "missing", "visibility": _visibility(t)})
        for t in FORBIDDEN_EXPORT_TARGETS:
            # enum should not include active cursor/platform targets as ExportTarget
            # allow string mentions in forbidden lists
            active_enum = f'PLATFORM = "{t}"' in text or f'CURSOR = "{t}"' in text
            add_check(
                checks,
                defects,
                f"exports:forbidden_not_active:{t}",
                not active_enum,
                t,
                "exports",
            )

    # Public export manifest: platform/insights must be forbidden/excluded, not exported as public products
    manifest = monorepo / "public-export-manifest.yaml"
    if manifest.is_file():
        mt = manifest.read_text(encoding="utf-8")
        platform_forbidden = "forbidden_internal_paths:" in mt and "- platform/" in mt
        # No active export repository named codestrata-platform or codestrata-insights as public
        active_platform_export = bool(
            re.search(r"(?m)^\s*repository:\s*codestrata-platform\s*$", mt)
        ) or bool(re.search(r"(?m)^\s*-\s*name:\s*codestrata-platform\s*$", mt))
        active_insights_export = bool(
            re.search(r"(?m)^\s*repository:\s*codestrata-insights\s*$", mt)
        )
        add_check(
            checks,
            defects,
            "exports:manifest_no_platform_surface",
            platform_forbidden and not active_platform_export,
            "platform forbidden_internal / no public platform export",
            "exports",
            classification="public_export_includes_platform",
        )
        add_check(
            checks,
            defects,
            "exports:manifest_no_insights_as_public",
            not active_insights_export,
            "no codestrata-insights public export",
            "exports",
            classification="public_export_includes_insights",
        )
        # Cursor may appear only as retired commentary, not as an active export repository
        active_cursor = bool(re.search(r"(?m)^\s*repository:\s*codestrata-cursor\s*$", mt))
        add_check(
            checks,
            defects,
            "exports:manifest_no_cursor",
            not active_cursor,
            "no active codestrata-cursor export",
            "exports",
        )

    # Single router entrypoint
    router = monorepo / "scripts/export_repository.py"
    add_check(checks, defects, "exports:single_router", router.is_file(), "export_repository.py", "exports")
    return checks, defects, results


def _visibility(target: str) -> str:
    return {
        "community": "public_community",
        "infrastructure": "private",
        "insights": "private_internal",
    }.get(target, "unknown")
