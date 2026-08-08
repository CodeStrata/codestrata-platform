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


def dashboard_source_blob(monorepo: Path, extra: tuple[str, ...] = ()) -> str:
    from verification.community_insights_dashboard.contract import (
        DASHBOARD_SOURCE_FILES,
    )

    parts = list(DASHBOARD_SOURCE_FILES) + list(extra)
    return "\n".join(read_text(monorepo, rel) for rel in parts)
