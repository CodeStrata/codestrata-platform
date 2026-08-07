"""Change plan and managed-destination detection."""

from __future__ import annotations

import json
import os
from pathlib import Path

from repository_export.checksums import sha256_bytes
from repository_export.errors import (
    DestinationManifestInvalid,
    UnmanagedDestination,
    UnmanagedDestinationFile,
)
from repository_export.models import ChangePlan, PlannedFile
from repository_export.policy import (
    ARTIFACT_FILENAMES,
    MANIFEST_FILENAME,
    MANIFEST_SCHEMA_NAME,
    MANIFEST_SCHEMA_VERSION,
    TARGET,
)
from repository_export.prohibited_files import EXCLUDE_DIR_NAMES


def _iter_dest_files(root: Path) -> dict[str, Path]:
    files: dict[str, Path] = {}
    if not root.exists():
        return files
    for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        dirnames[:] = sorted(n for n in dirnames if n not in EXCLUDE_DIR_NAMES)
        for name in sorted(filenames):
            path = Path(dirpath) / name
            if path.is_symlink():
                continue
            if not path.is_file():
                continue
            rel = path.relative_to(root).as_posix()
            files[rel] = path
    return files


def load_managed_manifest(destination: Path) -> dict | None:
    manifest_path = destination / MANIFEST_FILENAME
    if not manifest_path.is_file():
        return None
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DestinationManifestInvalid("destination manifest invalid") from exc
    if not isinstance(data, dict):
        raise DestinationManifestInvalid("destination manifest invalid")
    if data.get("schema_name") != MANIFEST_SCHEMA_NAME:
        raise DestinationManifestInvalid("destination manifest schema mismatch")
    if data.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        raise DestinationManifestInvalid("destination manifest version mismatch")
    if data.get("target") != TARGET:
        raise DestinationManifestInvalid("destination manifest target mismatch")
    return data


def managed_paths_from_manifest(manifest: dict) -> set[str]:
    paths = {str(entry["path"]) for entry in manifest.get("files") or []}
    paths |= set(ARTIFACT_FILENAMES)
    return paths


def build_change_plan(
    *,
    destination: Path,
    desired: list[PlannedFile],
) -> ChangePlan:
    desired_map = {f.destination_path: f for f in desired}
    desired_set = set(desired_map)

    if not destination.exists():
        return ChangePlan(
            additions=sorted(desired_set),
            modifications=[],
            removals=[],
            unchanged=[],
            conflicts=[],
            unmanaged=[],
        )

    existing = _iter_dest_files(destination)
    existing_set = set(existing)

    manifest = load_managed_manifest(destination)
    if manifest is None:
        if existing_set:
            raise UnmanagedDestination("non-empty destination without export manifest")
        return ChangePlan(additions=sorted(desired_set))

    managed = managed_paths_from_manifest(manifest)
    unmanaged = sorted(existing_set - managed)
    if unmanaged:
        raise UnmanagedDestinationFile(
            f"unmanaged destination files present: {len(unmanaged)}"
        )

    plan = ChangePlan()
    for rel in sorted(desired_set - existing_set):
        plan.additions.append(rel)
    for rel in sorted(existing_set - desired_set):
        # Only remove previously managed paths
        if rel in managed:
            plan.removals.append(rel)
        else:
            plan.conflicts.append(rel)
    for rel in sorted(desired_set & existing_set):
        current = sha256_bytes(existing[rel].read_bytes())
        if current == desired_map[rel].sha256:
            plan.unchanged.append(rel)
        else:
            plan.modifications.append(rel)

    if plan.conflicts:
        raise UnmanagedDestinationFile("conflict paths detected")
    return plan
