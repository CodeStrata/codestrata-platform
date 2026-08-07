"""File permission policy for exported content."""

from __future__ import annotations

from pathlib import PurePosixPath

from repository_export.errors import PermissionNotAllowed
from repository_export.policy import (
    EXECUTABLE_NAMES,
    EXECUTABLE_SUFFIXES,
    MODE_EXECUTABLE,
    MODE_FILE,
)


def approved_mode_for(destination_path: str, *, is_script_content: bool = False) -> int:
    name = PurePosixPath(destination_path).name
    if name in EXECUTABLE_NAMES or name.endswith(EXECUTABLE_SUFFIXES):
        return MODE_EXECUTABLE
    if is_script_content and destination_path.startswith("scripts/"):
        return MODE_EXECUTABLE
    return MODE_FILE


def assert_safe_mode(mode: int) -> None:
    if mode & 0o6000:
        raise PermissionNotAllowed("setuid/setgid not allowed")
    if mode & 0o002:
        raise PermissionNotAllowed("world-writable not allowed")


def apply_mode(path_mode: int) -> int:
    """Normalize arbitrary source mode into approved category."""

    executable = bool(path_mode & 0o111)
    mode = MODE_EXECUTABLE if executable else MODE_FILE
    assert_safe_mode(mode)
    return mode
