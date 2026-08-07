"""Path normalization and Approach A mapping."""

from __future__ import annotations

from pathlib import Path, PurePosixPath

from repository_export.errors import CaseCollision, PathCollision, UnsafeDestination


def to_posix(rel: str) -> str:
    return rel.replace("\\", "/").strip("/")


def normalize_destination_path(rel: str) -> str:
    posix = to_posix(rel)
    if not posix:
        raise UnsafeDestination("empty destination path")
    parts = PurePosixPath(posix).parts
    if any(p in {"", ".", ".."} for p in parts) or ".." in posix:
        raise UnsafeDestination("path traversal rejected")
    if posix.startswith("/") or PurePosixPath(posix).is_absolute():
        raise UnsafeDestination("absolute destination path rejected")
    return PurePosixPath(*parts).as_posix()


def approach_a_map(source_rel: str) -> str | None:
    """Map ``infrastructure/...`` → destination-relative path, or None to omit."""

    rel = to_posix(source_rel)
    if not rel.startswith("infrastructure/"):
        return None
    rest = rel[len("infrastructure/") :]
    if not rest:
        return None
    # Monorepo package marker is not useful at Approach A root.
    if rest == "__init__.py":
        return None
    # Source .gitignore is replaced by generated Infrastructure-specific file.
    if rest == ".gitignore":
        return None
    return normalize_destination_path(rest)


def ensure_unique_mappings(dest_to_source: dict[str, str]) -> None:
    """Fail on duplicate destination paths or case-insensitive collisions."""

    seen_lower: dict[str, str] = {}
    for dest, source in sorted(dest_to_source.items()):
        key = dest.lower()
        if key in seen_lower and seen_lower[key] != dest:
            raise CaseCollision(f"case collision: {seen_lower[key]} vs {dest}")
        seen_lower[key] = dest
    # dest_to_source keys must already be unique; double-check inverse
    inverse: dict[str, str] = {}
    for dest, source in dest_to_source.items():
        if dest in inverse and inverse[dest] != source:
            raise PathCollision(f"duplicate mapping for {dest}")
        inverse[dest] = source


def resolve_under(root: Path, rel: str) -> Path:
    """Resolve ``root/rel`` and ensure containment."""

    normalized = normalize_destination_path(rel)
    root_res = root.resolve()
    dest = (root_res / normalized).resolve()
    try:
        dest.relative_to(root_res)
    except ValueError as exc:
        raise UnsafeDestination("destination escapes root") from exc
    return dest
