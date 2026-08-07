"""Community target adapter — preserves multi-repo staging semantics."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from repository_export_router.destination import (
    require_destination,
    validate_destination_not_in_source,
)
from repository_export_router.errors import TargetExportFailed
from repository_export_router.models import RouterResult
from repository_export_router.ownership import assert_destination_compatible
from repository_export_router.targets import TARGET_REGISTRY, ExportTarget


def _load_public_export_module():
    scripts = Path(__file__).resolve().parents[1]
    path = scripts / "export-public-repos.py"
    spec = importlib.util.spec_from_file_location("codestrata_export_public_repos", path)
    if spec is None or spec.loader is None:
        raise TargetExportFailed("community_exporter_unavailable")
    module = importlib.util.module_from_spec(spec)
    # Register before exec so dataclasses in the module resolve correctly.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def export_community_target(
    *,
    destination: Path,
    dry_run: bool,
    source_root: Path,
) -> RouterResult:
    desc = TARGET_REGISTRY[ExportTarget.COMMUNITY]
    dest = require_destination(destination)
    validate_destination_not_in_source(source_root=source_root, destination=dest)
    assert_destination_compatible(target=ExportTarget.COMMUNITY, destination=dest)

    module = _load_public_export_module()
    code = module.run_public_export(staging=dest, dry_run=dry_run)
    if code != 0:
        raise TargetExportFailed("community_export_failed")

    # Count sibling export names from public manifest (deterministic metadata).
    manifest = module._load_manifest(module.DEFAULT_MANIFEST)
    export_names = [str(item.get("name")) for item in manifest.get("exports") or []]
    managed = len(export_names)

    return RouterResult(
        target=ExportTarget.COMMUNITY.value,
        status="ok",
        dry_run=dry_run,
        target_policy_version="community_release_2",
        target_manifest_schema=desc.manifest_schema,
        visibility=desc.visibility,
        destination_semantics=desc.destination_semantics,
        managed_file_count=managed,
        additions=0 if dry_run else managed,
        modifications=0,
        removals=0,
        conflicts=0,
        limitation_codes=[
            "community_exports_multiple_repositories_under_staging_root",
            "legacy_export_public_repos_compatibility_retained",
            "no_remote_repository_created",
        ],
    )
