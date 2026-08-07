"""Destination path safety checks."""

from __future__ import annotations

import os
from pathlib import Path

from repository_export.errors import (
    DestinationInsideSource,
    DestinationSymlink,
    UnsafeDestination,
)


def _is_home(path: Path) -> bool:
    try:
        return path.resolve() == Path.home().resolve()
    except OSError:
        return False


def validate_destination(*, source_root: Path, destination: Path) -> Path:
    """Validate and return resolved destination path.

    Rejects destinations inside the source repository, symlinks, filesystem
    root, home directory, and unsafe traversal.
    """

    if destination is None:
        raise UnsafeDestination("missing destination")

    raw = Path(destination)
    if str(raw) in {"", ".", "./"}:
        raise UnsafeDestination("destination must be explicit")

    # Reject symlink destinations before resolve follows them.
    if raw.exists() and raw.is_symlink():
        raise DestinationSymlink("destination is a symlink")
    if raw.parent.exists() and any(p.is_symlink() for p in raw.parents if p != raw.anchor):
        # If any parent is a symlink, resolve may escape; check after resolve.
        pass

    try:
        dest_resolved = raw.resolve(strict=False)
    except OSError as exc:
        raise UnsafeDestination("destination cannot be resolved") from exc

    source_resolved = source_root.resolve()

    if dest_resolved == source_resolved:
        raise DestinationInsideSource("destination is source root")

    try:
        dest_resolved.relative_to(source_resolved)
        raise DestinationInsideSource("destination is inside source repository")
    except ValueError:
        pass

    # Reject if source is inside destination (would overwrite repo when replacing)
    try:
        source_resolved.relative_to(dest_resolved)
        raise UnsafeDestination("destination would contain source repository")
    except ValueError:
        pass

    if dest_resolved == dest_resolved.anchor or str(dest_resolved) in {"/", "\\"}:
        raise UnsafeDestination("filesystem root rejected")

    if _is_home(dest_resolved):
        raise UnsafeDestination("home directory rejected")

    # Parent symlink into source
    parent = dest_resolved.parent
    if parent.exists():
        parent_res = parent.resolve()
        try:
            parent_res.relative_to(source_resolved)
            raise DestinationInsideSource("destination parent resolves inside source")
        except ValueError:
            pass
        if parent.is_symlink():
            raise DestinationSymlink("destination parent is a symlink")

    if dest_resolved.exists() and dest_resolved.is_file():
        raise UnsafeDestination("destination exists as a file; directory required")

    # cwd when unsafe: identical to source
    try:
        cwd = Path.cwd().resolve()
        if dest_resolved == cwd and cwd == source_resolved:
            raise UnsafeDestination("current working directory is source root")
    except OSError:
        pass

    # Reject path components with nul
    if "\x00" in str(raw):
        raise UnsafeDestination("nul in destination path")

    return dest_resolved


def discover_source_root(explicit: Path | None = None) -> Path:
    """Locate monorepo root containing infrastructure/docs/repository-contract.md."""

    if explicit is not None:
        root = explicit.resolve()
        contract = root / "infrastructure" / "docs" / "repository-contract.md"
        if not contract.is_file():
            from repository_export.errors import SourceRootInvalid

            raise SourceRootInvalid("source root missing infrastructure contract")
        if not (root / "infrastructure").is_dir():
            from repository_export.errors import SourceLayoutInvalid

            raise SourceLayoutInvalid("infrastructure/ missing")
        return root

    # Deterministic: this package lives at scripts/repository_export/
    here = Path(__file__).resolve()
    candidate = here.parents[2]
    contract = candidate / "infrastructure" / "docs" / "repository-contract.md"
    if contract.is_file() and (candidate / "infrastructure").is_dir():
        return candidate

    from repository_export.errors import SourceRootInvalid

    raise SourceRootInvalid("unable to discover source root")
