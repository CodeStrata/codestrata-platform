"""Atomic staging write for Infrastructure export."""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

from repository_export.errors import AtomicWriteFailed, SymlinkNotAllowed
from repository_export.models import PlannedFile
from repository_export.path_rules import resolve_under
from repository_export.permissions import assert_safe_mode


def write_tree(staging_root: Path, files: list[PlannedFile]) -> None:
    staging_root.mkdir(parents=True, exist_ok=True)
    for item in sorted(files, key=lambda f: f.destination_path):
        assert_safe_mode(item.mode)
        dest = resolve_under(staging_root, item.destination_path)
        if dest.exists() and dest.is_symlink():
            raise SymlinkNotAllowed("staging path is symlink")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(item.content)
        os.chmod(dest, item.mode)


def atomic_replace_destination(*, destination: Path, files: list[PlannedFile]) -> None:
    """Build complete tree in a sibling staging directory, then replace destination.

    Never deletes unmanaged destinations — caller must validate managed state first.
    """

    parent = destination.parent
    parent.mkdir(parents=True, exist_ok=True)
    staging: Path | None = None
    backup: Path | None = None
    try:
        staging = Path(
            tempfile.mkdtemp(prefix=".codestrata-infra-export-", dir=str(parent))
        )
        write_tree(staging, files)

        if destination.exists():
            backup = Path(
                tempfile.mkdtemp(prefix=".codestrata-infra-backup-", dir=str(parent))
            )
            # Move managed destination aside
            os.rename(destination, backup / "prev")
        os.rename(staging, destination)
        staging = None
        if backup is not None:
            shutil.rmtree(backup, ignore_errors=True)
            backup = None
    except OSError as exc:
        # Best-effort restore
        if backup is not None and (backup / "prev").exists() and not destination.exists():
            try:
                os.rename(backup / "prev", destination)
            except OSError:
                pass
        raise AtomicWriteFailed("atomic write failed") from exc
    finally:
        if staging is not None and staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
        if backup is not None and backup.exists():
            shutil.rmtree(backup, ignore_errors=True)
