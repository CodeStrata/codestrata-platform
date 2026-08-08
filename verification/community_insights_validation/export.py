"""Repository export checks."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from verification.community_insights_validation._common import add_check
from verification.community_insights_validation.models import CheckResult, Defect


def check_export(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    scripts = monorepo / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))

    from repository_export_router.router import export_repository
    from repository_export_router.targets import TARGET_REGISTRY, ExportTarget, parse_target
    from insights_repository_export.policy import INCLUDE_PREFIXES, SOURCE_ROOT_RELATIVE

    add_check(
        checks,
        defects,
        "export:target_registered",
        ExportTarget.INSIGHTS in TARGET_REGISTRY,
        "insights",
        "export",
    )
    add_check(
        checks,
        defects,
        "export:parse_insights",
        parse_target("insights") is ExportTarget.INSIGHTS,
        "ok",
        "export",
    )
    add_check(
        checks,
        defects,
        "export:source_root_insights_only",
        SOURCE_ROOT_RELATIVE == "insights",
        SOURCE_ROOT_RELATIVE,
        "export",
    )
    add_check(
        checks,
        defects,
        "export:inventory_excludes_platform_engine",
        "platform/" not in INCLUDE_PREFIXES and "engine/" not in INCLUDE_PREFIXES,
        "insights_only",
        "export",
    )
    add_check(
        checks,
        defects,
        "export:inventory_includes_insights_sources",
        "src/" in INCLUDE_PREFIXES and "public/" in INCLUDE_PREFIXES,
        "present",
        "export",
    )

    with tempfile.TemporaryDirectory(prefix="insights-validation-export-") as tmp:
        dest = Path(tmp) / "codestrata-insights"
        result = export_repository(
            target="insights",
            destination=dest,
            dry_run=True,
            source_root=monorepo,
        )
        add_check(
            checks,
            defects,
            "export:dry_run_ok",
            result.status == "ok" and result.dry_run is True,
            result.status,
            "export",
        )
        add_check(
            checks,
            defects,
            "export:private_visibility",
            result.visibility == "private_internal_application",
            result.visibility,
            "export",
        )
        add_check(
            checks,
            defects,
            "export:no_git_limitation",
            "no_git_init" in result.limitation_codes,
            "present",
            "export",
        )
        add_check(
            checks,
            defects,
            "export:managed_files_present",
            result.managed_file_count > 0,
            str(result.managed_file_count),
            "export",
        )
    return checks, defects
