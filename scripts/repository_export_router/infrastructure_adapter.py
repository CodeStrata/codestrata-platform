"""Infrastructure target adapter — delegates to Slice 12.6 exporter."""

from __future__ import annotations

import sys
from pathlib import Path

from repository_export_router.destination import (
    require_destination,
    validate_destination_not_in_source,
)
from repository_export_router.errors import TargetExportFailed, UnsafeDestination
from repository_export_router.models import RouterResult
from repository_export_router.ownership import assert_destination_compatible
from repository_export_router.targets import TARGET_REGISTRY, ExportTarget


def export_infrastructure_target(
    *,
    destination: Path,
    dry_run: bool,
    source_root: Path,
) -> RouterResult:
    desc = TARGET_REGISTRY[ExportTarget.INFRASTRUCTURE]
    dest = require_destination(destination)
    validate_destination_not_in_source(source_root=source_root, destination=dest)
    assert_destination_compatible(target=ExportTarget.INFRASTRUCTURE, destination=dest)

    scripts = Path(__file__).resolve().parents[1]
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))

    from repository_export.errors import ExportError
    from repository_export.exporter import export_infrastructure_repository

    try:
        result = export_infrastructure_repository(
            destination=dest,
            dry_run=dry_run,
            source_root=source_root,
        )
    except ExportError as exc:
        if exc.category in {
            "unsafe_destination",
            "destination_inside_source",
            "destination_symlink",
        }:
            raise UnsafeDestination(exc.category) from exc
        raise TargetExportFailed(exc.category) from exc

    d = result.diagnostics
    return RouterResult(
        target=ExportTarget.INFRASTRUCTURE.value,
        status=d.status,
        dry_run=dry_run,
        target_policy_version=d.source_policy_version,
        target_manifest_schema=desc.manifest_schema,
        visibility=desc.visibility,
        destination_semantics=desc.destination_semantics,
        managed_file_count=d.file_count,
        additions=d.addition_count,
        modifications=d.modification_count,
        removals=d.removal_count,
        conflicts=d.conflict_count,
        limitation_codes=list(d.limitation_codes),
    )
