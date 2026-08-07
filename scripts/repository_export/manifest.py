"""Export manifest and inventory builders."""

from __future__ import annotations

from typing import Any, Iterable

from repository_export.checksums import build_sha256sums, sha256_bytes
from repository_export.models import PlannedFile, dumps_canonical
from repository_export.policy import (
    ARTIFACT_FILENAMES,
    CHECKSUMS_FILENAME,
    DESTINATION_LAYOUT_VERSION,
    INVENTORY_FILENAME,
    MANIFEST_FILENAME,
    MANIFEST_SCHEMA_NAME,
    MANIFEST_SCHEMA_VERSION,
    REPOSITORY_NAME,
    SOURCE_LAYOUT_VERSION,
    TARGET,
    VALIDATION_COMMANDS,
    VALIDATION_ROOTS,
)


def build_inventory_records(files: Iterable[PlannedFile]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for item in sorted(files, key=lambda f: f.destination_path):
        if item.destination_path in ARTIFACT_FILENAMES:
            continue
        records.append(
            {
                "mode": item.mode_category,
                "path": item.destination_path,
                "sha256": item.sha256,
                "size": item.size,
                "source_classification": item.classification,
            }
        )
    return records


def build_checksum_map(files: Iterable[PlannedFile]) -> dict[str, str]:
    """Checksums for managed content excluding self-referential artifacts."""

    checksums: dict[str, str] = {}
    for item in files:
        if item.destination_path in ARTIFACT_FILENAMES:
            continue
        checksums[item.destination_path] = item.sha256
    return dict(sorted(checksums.items()))


def build_manifest(
    *,
    files: list[PlannedFile],
    excluded_categories: dict[str, int],
    limitations: list[str],
) -> dict[str, Any]:
    checksums = build_checksum_map(files)
    executable = sorted(
        f.destination_path
        for f in files
        if f.mode_category == "executable" and f.destination_path not in ARTIFACT_FILENAMES
    )
    file_entries = [
        {
            "classification": f.classification,
            "mode": f.mode_category,
            "path": f.destination_path,
            "sha256": f.sha256,
        }
        for f in sorted(files, key=lambda x: x.destination_path)
        if f.destination_path not in ARTIFACT_FILENAMES
    ]
    return {
        "checksums": checksums,
        "destination_layout_version": DESTINATION_LAYOUT_VERSION,
        "excluded_categories": dict(sorted(excluded_categories.items())),
        "executable_files": executable,
        "file_count": len(file_entries),
        "files": file_entries,
        "limitations": sorted(set(limitations)),
        "repository_name": REPOSITORY_NAME,
        "schema_name": MANIFEST_SCHEMA_NAME,
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "source_layout_version": SOURCE_LAYOUT_VERSION,
        "target": TARGET,
        "validation_commands": list(VALIDATION_COMMANDS),
        "validation_roots": list(VALIDATION_ROOTS),
    }


def attach_artifacts(
    managed: list[PlannedFile],
    *,
    excluded_categories: dict[str, int],
    limitations: list[str],
) -> list[PlannedFile]:
    """Append manifest, inventory, and SHA256SUMS as generated artifacts.

    Manifest describes managed content excluding the three artifact files.
    Inventory and SHA256SUMS likewise exclude themselves and each other from
    recursive self-hashing (checksums cover managed content only).
    """

    from repository_export.permissions import approved_mode_for

    manifest = build_manifest(
        files=managed,
        excluded_categories=excluded_categories,
        limitations=limitations,
    )
    inventory = {
        "file_count": len(build_inventory_records(managed)),
        "files": build_inventory_records(managed),
        "schema_name": "infrastructure-repository-export-inventory",
        "schema_version": "1.0.0",
    }
    checksums_text = build_sha256sums(build_checksum_map(managed))

    artifacts = [
        PlannedFile(
            destination_path=MANIFEST_FILENAME,
            content=dumps_canonical(manifest),
            mode=approved_mode_for(MANIFEST_FILENAME),
            classification="generated_artifact",
        ),
        PlannedFile(
            destination_path=INVENTORY_FILENAME,
            content=dumps_canonical(inventory),
            mode=approved_mode_for(INVENTORY_FILENAME),
            classification="generated_artifact",
        ),
        PlannedFile(
            destination_path=CHECKSUMS_FILENAME,
            content=checksums_text.encode("utf-8"),
            mode=approved_mode_for(CHECKSUMS_FILENAME),
            classification="generated_artifact",
        ),
    ]
    # Integrity: recompute sha via helper for tests
    _ = sha256_bytes(artifacts[0].content)
    return managed + artifacts
