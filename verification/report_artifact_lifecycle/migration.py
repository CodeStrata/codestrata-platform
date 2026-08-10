"""Migration checks for Slice 17.15."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.report_artifact_lifecycle.contract import ENGINE_LAYOUT
from verification.report_artifact_lifecycle.helpers import add_check, read_text
from verification.report_artifact_lifecycle.models import CheckResult, Defect

MIGRATION_MODULE = "engine/src/codestrata/artifacts/migration.py"


def check_migration(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {"migration_present": False, "legacy_alias_supported": False}

    mig_path = monorepo / MIGRATION_MODULE
    summary["migration_present"] = mig_path.is_file()
    add_check(
        checks,
        defects,
        "migration:module_exists",
        mig_path.is_file(),
        MIGRATION_MODULE,
        "migration",
    )

    if mig_path.is_file():
        text = read_text(mig_path)
        summary["legacy_alias_supported"] = "legacy" in text.lower() or "migrate" in text.lower()
        add_check(
            checks,
            defects,
            "migration:legacy_support",
            summary["legacy_alias_supported"],
            "legacy migration support",
            "migration",
            soft=False,
        )

    layout_path = monorepo / ENGINE_LAYOUT
    if layout_path.is_file():
        text = read_text(layout_path)
        has_legacy = "run_id" in text or "build_assessment_run_id" in text
        has_slots = "current" in text
        add_check(
            checks,
            defects,
            "migration:layout_transition",
            has_legacy or has_slots,
            "layout supports transition",
            "migration",
            soft=not has_slots,
        )

    return checks, defects, summary
