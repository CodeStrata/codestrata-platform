"""Monorepo extraction bootstrap / update hardening helpers."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import RELEASE_TOOLING_VERSION


def tree_fingerprint(root: Path) -> dict[str, str]:
    """Return relative-path -> sha256 for all regular files under root."""

    mapping: dict[str, str] = {}
    if not root.is_dir():
        return mapping
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        if ".git" in path.parts:
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        mapping[path.relative_to(root).as_posix()] = digest
    return mapping


def write_export_snapshot(
    *,
    staging_repo: Path,
    export_name: str,
    manifest_version: object,
    mode: str,
    source_commit: str | None = None,
) -> Path:
    """Write a bootstrap/update marker into a staged export repository."""

    fingerprint = tree_fingerprint(staging_repo)
    # Fingerprint must ignore the snapshot file itself when recomputed later.
    fingerprint = {
        key: value
        for key, value in fingerprint.items()
        if key != ".codestrata-export-snapshot.json"
    }
    payload = {
        "export_name": export_name,
        "manifest_version": manifest_version,
        "extraction_tooling_version": RELEASE_TOOLING_VERSION,
        "mode": mode,
        "source_commit": source_commit,
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace(
            "+00:00", "Z"
        ),
        "file_count": len(fingerprint),
        "content_fingerprint": hashlib.sha256(
            json.dumps(fingerprint, sort_keys=True).encode("utf-8")
        ).hexdigest(),
    }
    path = staging_repo / ".codestrata-export-snapshot.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def assert_idempotent_export(
    first: dict[str, str],
    second: dict[str, str],
) -> list[str]:
    """Compare two fingerprints; return human-readable differences."""

    errors: list[str] = []
    # Snapshot file itself may change timestamp fields — compare content sets
    # excluding the snapshot metadata file.
    def scrub(mapping: dict[str, str]) -> dict[str, str]:
        return {
            key: value
            for key, value in mapping.items()
            if key != ".codestrata-export-snapshot.json"
        }

    a = scrub(first)
    b = scrub(second)
    if a.keys() != b.keys():
        missing = sorted(set(a) - set(b))
        extra = sorted(set(b) - set(a))
        if missing:
            errors.append(f"missing after re-export: {missing[:10]}")
        if extra:
            errors.append(f"extra after re-export: {extra[:10]}")
    changed = sorted(key for key in (set(a) & set(b)) if a[key] != b[key])
    if changed:
        errors.append(f"content changed after re-export: {changed[:10]}")
    return errors


def bootstrap_status(staging_repo: Path) -> dict[str, Any]:
    """Describe whether staging looks like first-time or update-ready."""

    exists = staging_repo.is_dir()
    files = list(staging_repo.rglob("*")) if exists else []
    file_count = sum(1 for path in files if path.is_file())
    snapshot = staging_repo / ".codestrata-export-snapshot.json"
    return {
        "path": staging_repo.name,
        "exists": exists,
        "file_count": file_count,
        "mode": "update" if file_count else "first_time",
        "snapshot_present": snapshot.is_file(),
    }
