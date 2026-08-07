"""Shared destination safety for the router (target adapters may add more)."""

from __future__ import annotations

from pathlib import Path

from repository_export_router.errors import MissingDestination, UnsafeDestination


def require_destination(raw: Path | None) -> Path:
    if raw is None or str(raw).strip() in {"", ".", "./"}:
        raise MissingDestination("missing_destination")
    return Path(raw)


def validate_destination_not_in_source(*, source_root: Path, destination: Path) -> Path:
    """Basic containment checks shared by both targets."""

    try:
        dest = destination.resolve(strict=False)
        source = source_root.resolve()
    except OSError as exc:
        raise UnsafeDestination("unsafe_destination") from exc

    if dest == source:
        raise UnsafeDestination("unsafe_destination")
    try:
        dest.relative_to(source)
        raise UnsafeDestination("unsafe_destination")
    except ValueError:
        pass
    try:
        source.relative_to(dest)
        raise UnsafeDestination("unsafe_destination")
    except ValueError:
        pass
    if dest == dest.anchor or str(dest) in {"/", "\\"}:
        raise UnsafeDestination("unsafe_destination")
    if destination.exists() and destination.is_symlink():
        raise UnsafeDestination("unsafe_destination")
    return dest
