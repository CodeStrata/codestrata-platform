"""Active Cursor release-surface inventory helpers for Slice 12.2."""

from __future__ import annotations

from pathlib import Path
from typing import Any

# Relative paths that previously held active Cursor build/release/Marketplace refs.
REMOVED_ACTIVE_SURFACES: tuple[str, ...] = (
    "verification/release_artifacts/cursor_extension.py",
    "public-export-manifest.yaml#codestrata-cursor",
    "scripts/release/versions.py#cursor_extension",
    "scripts/release/dependencies.py#codestrata-cursor",
    "scripts/release/licensing.py#cursor-plugin",
    "scripts/release/inventory.py#cursor-plugin/",
    "governance/assets/extension-branding/MARKETPLACE_PUBLICATION.md#cursor-publish",
    "vscode-plugin/MARKETPLACE.md#cursor-publish",
)

ACTIVE_SCAN_ROOTS: tuple[str, ...] = (
    "scripts/release",
    "verification/release_artifacts",
    "public-export-manifest.yaml",
)

FORBIDDEN_ACTIVE_TOKENS: tuple[str, ...] = (
    "cursor-plugin",
    "codestrata-cursor",
    "check_cursor_extension",
    "cursor_extension:",
)


def scan_active_surfaces(monorepo: Path) -> dict[str, Any]:
    hits: list[str] = []
    for rel in ACTIVE_SCAN_ROOTS:
        path = monorepo / rel
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="ignore")
            for token in FORBIDDEN_ACTIVE_TOKENS:
                if token in text and "retired" not in text.lower():
                    # Allow retirement comments that mention historical names.
                    for line in text.splitlines():
                        if token in line and "retired" not in line.lower() and not line.strip().startswith("#"):
                            # Comment-only historical notes in YAML header are ok if they say retired
                            if "retired" in text.lower() and path.name == "public-export-manifest.yaml":
                                continue
                            hits.append(f"{rel}:{token}")
                            break
        elif path.is_dir():
            for child in sorted(path.rglob("*")):
                if not child.is_file():
                    continue
                if child.suffix.lower() not in {".py", ".md", ".yaml", ".yml", ".json", ".sh"}:
                    continue
                text = child.read_text(encoding="utf-8", errors="ignore")
                for token in FORBIDDEN_ACTIVE_TOKENS:
                    if token in text:
                        rel_child = str(child.relative_to(monorepo))
                        # Historical Slice 12.1 package may mention cursor-plugin absence — allow
                        if "cursor_extension_removal" in rel_child:
                            continue
                        hits.append(f"{rel_child}:{token}")
                        break
    return {
        "hits": sorted(set(hits)),
        "removed_surface_count": len(REMOVED_ACTIVE_SURFACES),
        "active_editor_extensions": ["codestrata-assessment"],
    }
