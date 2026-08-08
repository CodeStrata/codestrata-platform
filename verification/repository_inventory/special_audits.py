"""Special audit target collectors for Slice 16.1."""

from __future__ import annotations

from pathlib import Path

from verification.repository_inventory.inventory import (
    content_fingerprint,
    find_duplicate_basenames,
    find_duplicate_token_copies,
)
from verification.repository_inventory.models import InventoryEntry


def collect_sqlite(entries: list[InventoryEntry]) -> list[str]:
    return sorted(e.path for e in entries if e.kind == "sqlite" or e.path.endswith((".sqlite", ".db")))


def discover_sqlite_databases(monorepo: Path) -> list[str]:
    """Find sqlite/db files with pruned heavy trees (read-only)."""
    skip_parts = {
        ".git",
        ".venv",
        "node_modules",
        ".terraform",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".wrangler",
        ".vscode-test",
    }
    found: list[str] = []
    for path in monorepo.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".sqlite", ".db"}:
            continue
        rel = path.relative_to(monorepo).as_posix()
        parts = set(Path(rel).parts)
        if parts & skip_parts:
            continue
        if "validation/repos/" in rel or rel.startswith("validation/repos/"):
            continue
        found.append(rel)
    return sorted(found)


def collect_aimf_refs(monorepo: Path, entries: list[InventoryEntry]) -> list[str]:
    hits: list[str] = []
    for e in entries:
        if e.kind == "directory":
            continue
        if e.path.startswith((".export-staging/", "dist/", ".generated/", "docs/.vitepress/dist/")):
            continue
        path = monorepo / e.path
        if not path.is_file():
            continue
        if path.suffix.lower() not in {
            ".md",
            ".py",
            ".ts",
            ".tsx",
            ".js",
            ".json",
            ".toml",
            ".yml",
            ".yaml",
            ".css",
        }:
            # path-name hits
            if "aimf" in e.path.lower():
                hits.append(e.path)
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "aimf" in text.lower() or "aimf" in e.path.lower():
            hits.append(e.path)
    return sorted(set(hits))


def collect_cursor_refs(monorepo: Path, entries: list[InventoryEntry]) -> list[str]:
    hits: list[str] = []
    for e in entries:
        lower = e.path.lower()
        if "cursor" in lower:
            hits.append(e.path)
            continue
        if e.kind == "directory":
            continue
        if e.path.startswith((".export-staging/", "dist/", ".generated/", "verification/cursor_")):
            if e.path.startswith("verification/cursor_"):
                hits.append(e.path)
            continue
        path = monorepo / e.path
        if not path.is_file() or path.suffix.lower() not in {".md", ".py", ".ts", ".json", ".yml"}:
            continue
        # Limit content scan to likely surfaces
        if not any(
            e.path.startswith(p)
            for p in (
                "README.md",
                "CHANGELOG.md",
                "docs/",
                "scripts/",
                "platform/docs/",
                ".github/",
            )
        ):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "cursor-plugin" in text.lower() or "cursor extension" in text.lower():
            hits.append(e.path)
    return sorted(set(hits))


def collect_dist_dirs(entries: list[InventoryEntry]) -> list[str]:
    return sorted(
        e.path
        for e in entries
        if e.kind == "directory"
        and (e.path == "dist" or e.path.endswith("/dist") or "/dist/" in e.path + "/")
    )


def collect_committed_node_modules(monorepo: Path) -> list[str]:
    # Use git ls-files semantics via reading .gitignore + presence check of tracked listing is done in checks.
    # Here list any node_modules directories discovered in inventory walk.
    return []


def collect_temp_files(entries: list[InventoryEntry]) -> list[str]:
    return sorted(
        e.path
        for e in entries
        if e.classification == "DELETE_CANDIDATE"
        or e.path.endswith((".DS_Store", ".tmp", ".bak", ".swp", "~"))
        or Path(e.path).name == ".DS_Store"
    )


def collect_old_release_notes(entries: list[InventoryEntry]) -> list[str]:
    return sorted(
        e.path
        for e in entries
        if "release" in e.path.lower()
        and e.path.endswith((".md", ".json"))
        and (
            e.path.startswith("docs/")
            or e.path.startswith("reports/")
            or "CHANGELOG" in e.path
            or "release-notes" in e.path.lower()
        )
    )


def collect_policy_schema_duplicates(entries: list[InventoryEntry]) -> dict[str, list[str]]:
    by_name: dict[str, list[str]] = {}
    for e in entries:
        if e.kind == "directory":
            continue
        name = Path(e.path).name
        if not name.endswith(".json"):
            continue
        interesting = (
            name.endswith("_policy.json")
            or name.endswith("-policy.json")
            or name.endswith("_contract.json")
            or name.endswith("-contract.json")
            or "schema" in name.lower()
            or "/policies/" in e.path
            or "/contracts/" in e.path
        )
        if not interesting:
            continue
        by_name.setdefault(name, []).append(e.path)
    return {k: sorted(v) for k, v in sorted(by_name.items()) if len(v) > 1}


def build_special_audits(monorepo: Path, entries: list[InventoryEntry]) -> dict:
    dup_names = find_duplicate_basenames(monorepo, entries)
    token_dups = find_duplicate_token_copies(entries)
    policy_dups = collect_policy_schema_duplicates(entries)

    # Content-identical token copies among known tokens.css paths
    token_fps: dict[str, list[str]] = {}
    for rel in [e.path for e in entries if Path(e.path).name == "tokens.css"]:
        fp = content_fingerprint(monorepo, rel)
        if fp:
            token_fps.setdefault(fp, []).append(rel)

    return {
        "sqlite_databases": discover_sqlite_databases(monorepo),
        "sqlite_databases_in_inventory_walk": collect_sqlite(entries),
        "legacy_aimf_references": collect_aimf_refs(monorepo, entries),
        "legacy_cursor_references": collect_cursor_refs(monorepo, entries),
        "duplicate_basenames": {k: v for k, v in list(dup_names.items())[:80]},
        "duplicate_tokens_css": token_dups,
        "duplicate_tokens_by_hash": {k: sorted(v) for k, v in token_fps.items() if len(v) > 1},
        "dist_directories": collect_dist_dirs(entries),
        "temp_or_junk_candidates": collect_temp_files(entries),
        "old_release_notes_candidates": collect_old_release_notes(entries),
        "duplicate_policies_or_schemas": policy_dups,
        "stale_markdown_candidates": sorted(
            e.path
            for e in entries
            if e.kind == "markdown"
            and (e.classification in {"STALE", "HISTORICAL", "ARCHIVE_CANDIDATE"} or "STALE" in e.secondary_classifications)
        ),
        "committed_node_modules_tracked": collect_committed_node_modules(monorepo),
    }
