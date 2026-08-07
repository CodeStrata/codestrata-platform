"""Asset inventory helpers for Slice 13.12 (path-free public output)."""

from __future__ import annotations

import struct
from pathlib import Path

from verification.vscode_marketplace_branding.contract import (
    GALLERY_ORDER,
    ICON_HEIGHT,
    ICON_RELATIVE,
    ICON_WIDTH,
    PLUGIN_ROOT,
)


def plugin_root(monorepo: Path) -> Path:
    return monorepo / PLUGIN_ROOT


def media_dir(monorepo: Path) -> Path:
    return plugin_root(monorepo) / "media"


def png_dimensions(path: Path) -> tuple[int, int] | None:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    width, height = struct.unpack(">II", data[16:24])
    return int(width), int(height)


def asset_size_bytes(monorepo: Path, relative: str) -> int:
    path = plugin_root(monorepo) / relative
    try:
        return path.stat().st_size
    except OSError:
        return -1


def required_assets_present(monorepo: Path) -> list[str]:
    missing: list[str] = []
    root = plugin_root(monorepo)
    for rel in (ICON_RELATIVE, "media/codestrata-activity.svg", "media/marketplace-banner.png"):
        if not (root / rel).is_file():
            missing.append(rel)
    for rel in GALLERY_ORDER:
        if not (root / rel).is_file():
            missing.append(rel)
    return missing


def icon_ok(monorepo: Path) -> bool:
    path = plugin_root(monorepo) / ICON_RELATIVE
    dims = png_dimensions(path)
    return dims == (ICON_WIDTH, ICON_HEIGHT)


def marketplace_asset_total_bytes(monorepo: Path) -> int:
    total = 0
    for path in sorted(media_dir(monorepo).iterdir()):
        if path.suffix.lower() in {".png", ".svg"}:
            total += path.stat().st_size
    return total


def asset_inventory_stable(monorepo: Path) -> list[dict[str, object]]:
    """Deterministic inventory without absolute paths."""
    rows: list[dict[str, object]] = []
    for path in sorted(media_dir(monorepo).iterdir()):
        if path.suffix.lower() not in {".png", ".svg", ".md"}:
            continue
        rel = f"media/{path.name}"
        entry: dict[str, object] = {
            "name": path.name,
            "relative": rel,
            "bytes": path.stat().st_size,
            "kind": path.suffix.lower().lstrip("."),
        }
        if path.suffix.lower() == ".png":
            dims = png_dimensions(path)
            if dims:
                entry["width"] = dims[0]
                entry["height"] = dims[1]
        rows.append(entry)
    return rows
