"""Filesystem helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def exists(monorepo: Path, relative: str) -> bool:
    return (monorepo / relative).exists()


def load_json(monorepo: Path, relative: str) -> dict[str, Any]:
    path = monorepo / relative
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def read_text(monorepo: Path, relative: str) -> str:
    path = monorepo / relative
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def package_source_blob(monorepo: Path, relative_dir: str) -> str:
    root = monorepo / relative_dir
    if not root.is_dir():
        return ""
    parts: list[str] = []
    for path in sorted(root.rglob("*.py")):
        if path.is_file():
            parts.append(path.read_text(encoding="utf-8"))
    return "\n".join(parts)
