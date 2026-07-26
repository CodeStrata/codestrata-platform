"""Safe repository filesystem traversal helpers."""

from __future__ import annotations

import os
from pathlib import Path


def iter_repository_files(
    repository_root: Path,
    *,
    excluded_directories: set[str],
    max_files: int | None = None,
) -> list[str]:
    """Return sorted repo-relative file paths without following symlinks.

    Directory symlinks are not descended into. File symlinks are included only
    when their resolved target remains inside ``repository_root``.
    """

    root = repository_root.expanduser().resolve()
    collected: list[str] = []

    for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        current = Path(dirpath)
        # Prune excluded directories in-place (os.walk contract).
        dirnames[:] = sorted(
            name
            for name in dirnames
            if name not in excluded_directories and not (current / name).is_symlink()
        )

        for name in filenames:
            path = current / name
            if path.is_symlink():
                try:
                    target = path.resolve(strict=False)
                    target.relative_to(root)
                except (ValueError, OSError, RuntimeError):
                    continue
            elif not path.is_file():
                continue

            try:
                relative = path.relative_to(root).as_posix()
            except ValueError:
                continue

            if any(part in excluded_directories for part in relative.split("/")):
                continue

            collected.append(relative)
            if max_files is not None and len(collected) >= max_files:
                return sorted(collected)

    return sorted(collected)


def assert_path_within_root(candidate: Path, root: Path) -> Path:
    """Resolve ``candidate`` and ensure it stays under ``root``."""

    resolved_root = root.expanduser().resolve()
    resolved = candidate.expanduser().resolve(strict=False)
    try:
        resolved.relative_to(resolved_root)
    except ValueError as error:
        raise ValueError(
            f"path escapes allowed root {resolved_root}: {candidate}"
        ) from error
    return resolved


def safe_output_directory(path: Path, *, cwd: Path | None = None) -> Path:
    """Resolve an output directory under the process working directory by default.

    Absolute paths are allowed when they resolve successfully; the caller is
    responsible for user intent. Relative paths cannot escape via ``..`` beyond
    the resolved absolute location (resolve collapses ``..``).
    """

    base = (cwd or Path.cwd()).resolve()
    raw = path.expanduser()
    if not raw.is_absolute():
        candidate = (base / raw).resolve(strict=False)
    else:
        candidate = raw.resolve(strict=False)
    candidate.mkdir(parents=True, exist_ok=True)
    if not candidate.is_dir():
        raise NotADirectoryError(f"output path is not a directory: {candidate}")
    return candidate
