"""Deterministic repository walk and inventory assembly (read-only)."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from pathlib import Path

from verification.repository_inventory.classifier import (
    AUTHORITATIVE_TOKENS,
    area_for_path,
    classify_path,
    kind_for_path,
)
from verification.repository_inventory.contract import (
    INVENTORY_AREAS,
    MAX_FILES_PER_AREA,
    PRUNE_DIR_NAMES,
)
from verification.repository_inventory.models import InventoryEntry

SIGNIFICANT_ROOT_FILES = (
    "README.md",
    "ARCHITECTURE.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "ROADMAP.md",
    "pyproject.toml",
    "codestrata.toml",
    "docker-compose.yml",
    "public-export-manifest.yaml",
    ".gitignore",
    ".env.example",
)

TOP_LEVEL_AREAS = (
    "engine",
    "platform",
    "infrastructure",
    "vscode-plugin",
    "insights",
    "docs",
    "design-system",
    "verification",
    "tests",
    "reports",
    "scripts",
    "governance",
    "knowledge",
    "examples",
    "validation",
    "test-fixtures",
    ".export-staging",
    ".generated",
    "dist",
    ".codestrata",
    ".codestrata-examples",
    ".codestrata-test-knowledge",
    ".cursor",
)

ASSET_BASENAME_HINTS = (
    "icon",
    "logo",
    "screenshot",
    "favicon",
    "tokens.css",
    "mark.svg",
    "wordmark",
)


def _rel(monorepo: Path, path: Path) -> str:
    return path.relative_to(monorepo).as_posix()


def _should_prune(name: str, parent_rel: str) -> bool:
    if name in PRUNE_DIR_NAMES:
        # Only prune validation/repos, not every "repos" folder.
        if name == "repos":
            return parent_rel == "validation" or parent_rel.startswith("validation/")
        return True
    return False


def walk_significant_paths(monorepo: Path) -> list[tuple[str, bool, bool]]:
    """Return sorted list of (relative_path, is_dir, is_empty_dir)."""
    found: list[tuple[str, bool, bool]] = []

    for name in SIGNIFICANT_ROOT_FILES:
        p = monorepo / name
        if p.is_file():
            found.append((name, False, False))

    for top in TOP_LEVEL_AREAS:
        root = monorepo / top
        if not root.exists():
            continue
        if root.is_file():
            found.append((top, False, False))
            continue
        # Area root directory entry
        children = list(root.iterdir()) if root.is_dir() else []
        found.append((top, True, len(children) == 0))

        # Bulk stubs for pruned heavy trees
        if top == "validation":
            repos = root / "repos"
            if repos.is_dir():
                found.append(
                    (
                        "validation/repos",
                        True,
                        False,
                    )
                )
            # continue walking non-repos under validation
        if top == ".export-staging":
            for child in sorted(root.iterdir(), key=lambda p: p.name):
                rel = _rel(monorepo, child)
                if child.is_dir():
                    found.append((rel, True, not any(child.iterdir())))
                    # sample key nested markers without full deep walk of export trees
                    for marker in (
                        "media",
                        "src",
                        "public",
                        ".codestrata",
                        ".vitepress",
                    ):
                        m = child / marker
                        if m.exists():
                            found.append((_rel(monorepo, m), m.is_dir(), False))
            continue
        if top in {".generated", "dist", ".codestrata", ".codestrata-test-knowledge", ".mypy_cache"}:
            continue

        file_count = 0
        stack = [root]
        while stack:
            current = stack.pop()
            try:
                entries = sorted(current.iterdir(), key=lambda p: p.name)
            except PermissionError:
                continue
            for entry in entries:
                rel = _rel(monorepo, entry)
                parent_rel = _rel(monorepo, current)
                if entry.is_dir():
                    if _should_prune(entry.name, parent_rel):
                        found.append((rel, True, False))
                        continue
                    # skip deep terraform providers
                    if entry.name == ".terraform":
                        found.append((rel, True, False))
                        continue
                    empty = not any(entry.iterdir())
                    found.append((rel, True, empty))
                    stack.append(entry)
                else:
                    file_count += 1
                    if file_count > MAX_FILES_PER_AREA:
                        continue
                    found.append((rel, False, False))

    # Deduplicate preserving order then sort for determinism
    seen: set[str] = set()
    unique: list[tuple[str, bool, bool]] = []
    for item in found:
        if item[0] in seen:
            continue
        seen.add(item[0])
        unique.append(item)
    unique.sort(key=lambda t: t[0])
    return unique


def build_entries(monorepo: Path) -> list[InventoryEntry]:
    entries: list[InventoryEntry] = []
    for rel, is_dir, empty in walk_significant_paths(monorepo):
        primary, notes, secondary = classify_path(rel, is_dir=is_dir, empty=empty)
        entries.append(
            InventoryEntry(
                path=rel,
                area=area_for_path(rel),
                kind=kind_for_path(rel, is_dir),
                classification=primary,
                notes=notes,
                secondary_classifications=sorted(set(secondary)),
            )
        )
    return entries


def content_fingerprint(monorepo: Path, rel: str, *, limit: int = 65536) -> str | None:
    path = monorepo / rel
    if not path.is_file():
        return None
    try:
        data = path.read_bytes()[:limit]
    except OSError:
        return None
    return hashlib.sha256(data).hexdigest()


def find_duplicate_basenames(monorepo: Path, entries: list[InventoryEntry]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = defaultdict(list)
    for e in entries:
        if e.kind == "directory":
            continue
        name = Path(e.path).name.lower()
        interesting = e.kind in {"asset", "css"} or any(h in name for h in ASSET_BASENAME_HINTS)
        if not interesting:
            continue
        groups[name].append(e.path)
    return {k: sorted(v) for k, v in sorted(groups.items()) if len(v) > 1}


def find_duplicate_token_copies(entries: list[InventoryEntry]) -> list[str]:
    return sorted(
        e.path
        for e in entries
        if Path(e.path).name == "tokens.css" and e.path != AUTHORITATIVE_TOKENS
    )


def classification_counts(entries: list[InventoryEntry]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for e in entries:
        counts[e.classification] += 1
        for s in e.secondary_classifications:
            counts[s] += 0  # ensure key presence without double-counting primary
    # Ensure all expected keys appear with at least 0 after merge in runner
    return dict(sorted(counts.items()))


def area_counts(entries: list[InventoryEntry]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for e in entries:
        counts[e.area] += 1
    # Ensure inventory areas present
    for area in INVENTORY_AREAS:
        counts.setdefault(area, 0)
    return dict(sorted(counts.items()))


def candidates_by_class(entries: list[InventoryEntry], name: str) -> list[str]:
    out: list[str] = []
    for e in entries:
        if e.classification == name or name in e.secondary_classifications:
            out.append(e.path)
    return sorted(set(out))
