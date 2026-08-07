"""Infrastructure repository export orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from repository_export.change_plan import build_change_plan
from repository_export.destination_layout import discover_source_root, validate_destination
from repository_export.errors import ExportError
from repository_export.manifest import attach_artifacts
from repository_export.models import ChangePlan, ExportDiagnostics, PlannedFile
from repository_export.policy import (
    MANIFEST_SCHEMA_VERSION,
    POLICY_VERSION,
    TARGET,
)
from repository_export.root_files import build_generated_root_files
from repository_export.source_inventory import collect_source_inventory, materialize_source_files
from repository_export.writer import atomic_replace_destination


@dataclass
class ExportResult:
    diagnostics: ExportDiagnostics
    change_plan: ChangePlan
    files: list[PlannedFile]
    limitations: list[str]


def build_desired_export(source_root: Path) -> tuple[list[PlannedFile], list[str], dict[str, int]]:
    inventory = collect_source_inventory(source_root)
    planned = materialize_source_files(inventory)

    # README handled by root generation (Approach A header + doc rewrites)
    planned = [f for f in planned if f.destination_path != "README.md"]
    readme_bytes = (source_root / "infrastructure" / "README.md").read_bytes()
    generated = build_generated_root_files(source_root=source_root, readme_source=readme_bytes)

    # Merge: generated root files win on path collisions with mapped content
    by_path = {f.destination_path: f for f in planned}
    for item in generated:
        by_path[item.destination_path] = item
    merged = [by_path[k] for k in sorted(by_path)]

    limitations = sorted(set(inventory.limitations))
    limitations.extend(
        [
            "destination_repository_not_created",
            "opentofu_validation_deferred_to_12_7",
            "no_remote_repository_configured",
            "ci_integration_deferred_to_12_9",
            "source_cutover_not_performed",
        ]
    )
    with_artifacts = attach_artifacts(
        merged,
        excluded_categories=inventory.excluded_categories,
        limitations=sorted(set(limitations)),
    )
    return with_artifacts, sorted(set(limitations)), inventory.excluded_categories


def export_infrastructure_repository(
    *,
    destination: Path,
    dry_run: bool = False,
    source_root: Path | None = None,
) -> ExportResult:
    root = discover_source_root(source_root)
    dest = validate_destination(source_root=root, destination=destination)

    files, limitations, excluded = build_desired_export(root)
    plan = build_change_plan(destination=dest, desired=files)

    generated_count = sum(
        1
        for f in files
        if f.classification in {"generated_root_file", "generated_artifact", "transformed_export"}
    )
    executable_count = sum(1 for f in files if f.mode_category == "executable")

    diagnostics = ExportDiagnostics(
        target=TARGET,
        status="ok",
        dry_run=dry_run,
        source_policy_version=POLICY_VERSION,
        manifest_schema_version=MANIFEST_SCHEMA_VERSION,
        file_count=len(files),
        generated_file_count=generated_count,
        executable_file_count=executable_count,
        excluded_category_count=len(excluded),
        addition_count=len(plan.additions),
        modification_count=len(plan.modifications),
        removal_count=len(plan.removals),
        conflict_count=len(plan.conflicts),
        limitation_codes=sorted(set(limitations)),
    )

    if dry_run:
        return ExportResult(
            diagnostics=diagnostics,
            change_plan=plan,
            files=files,
            limitations=sorted(set(limitations)),
        )

    atomic_replace_destination(destination=dest, files=files)
    return ExportResult(
        diagnostics=diagnostics,
        change_plan=plan,
        files=files,
        limitations=sorted(set(limitations)),
    )


def export_or_raise(**kwargs: Any) -> ExportResult:
    try:
        return export_infrastructure_repository(**kwargs)
    except ExportError:
        raise
