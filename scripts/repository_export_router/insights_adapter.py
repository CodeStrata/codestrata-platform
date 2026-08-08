"""Adapter for Insights router target."""

from __future__ import annotations

import sys
from pathlib import Path

from repository_export_router.destination import (
    require_destination,
    validate_destination_not_in_source,
)
from repository_export_router.models import RouterResult
from repository_export_router.ownership import assert_destination_compatible
from repository_export_router.targets import TARGET_REGISTRY, ExportTarget


def export_insights_target(
    *,
    destination: Path,
    dry_run: bool = False,
    source_root: Path,
) -> RouterResult:
    desc = TARGET_REGISTRY[ExportTarget.INSIGHTS]
    dest = require_destination(destination)
    validate_destination_not_in_source(source_root=source_root, destination=dest)
    assert_destination_compatible(target=ExportTarget.INSIGHTS, destination=dest)

    scripts = Path(__file__).resolve().parents[1]
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))

    from insights_repository_export.exporter import export_insights_repository
    from insights_repository_export.policy import POLICY_VERSION

    result = export_insights_repository(
        destination=dest,
        dry_run=dry_run,
        source_root=source_root,
    )
    return RouterResult(
        target=ExportTarget.INSIGHTS.value,
        status=result.diagnostics.status,
        dry_run=dry_run,
        target_policy_version=POLICY_VERSION,
        target_manifest_schema=desc.manifest_schema,
        visibility=desc.visibility,
        destination_semantics=desc.destination_semantics,
        managed_file_count=result.diagnostics.file_count,
        additions=result.diagnostics.file_count if not dry_run else 0,
        modifications=0,
        removals=0,
        conflicts=0,
        limitation_codes=list(result.limitations),
    )
