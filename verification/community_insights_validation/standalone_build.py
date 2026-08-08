"""Standalone build inventory checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_validation._common import add_check
from verification.community_insights_validation.contract import APP_ROOT
from verification.community_insights_validation.inventory import exists, load_json
from verification.community_insights_validation.models import CheckResult, Defect


def check_standalone_build(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    add_check(
        checks,
        defects,
        "standalone:app_root",
        exists(monorepo, APP_ROOT),
        APP_ROOT,
        "export",
    )
    for rel in (
        "insights/package.json",
        "insights/vite.config.ts",
        "insights/src/main.tsx",
        "insights/index.html",
    ):
        add_check(
            checks,
            defects,
            f"standalone:file:{Path(rel).name}",
            exists(monorepo, rel),
            rel,
            "export",
        )
    pkg = load_json(monorepo, "insights/package.json")
    scripts = pkg.get("scripts") or {}
    add_check(
        checks,
        defects,
        "standalone:build_script",
        "build" in scripts and "test" in scripts,
        "present",
        "export",
    )
    return checks, defects
