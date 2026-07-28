#!/usr/bin/env python3
"""Export public mirror repositories from codestrata-platform (staging only).

Does not create, push, or publish GitHub repositories.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import os
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    print("PyYAML is required: pip install PyYAML", file=sys.stderr)
    raise SystemExit(2) from None

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "public-export-manifest.yaml"

# Directory names pruned during source walks so generated trees are never copied.
_PRUNE_DIR_NAMES = frozenset(
    {
        ".git",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".codestrata",
        ".codestrata-examples",
        ".codestrata-test-knowledge",
        ".venv",
        "venv",
        "node_modules",
        "dist",
        "build",
        ".eggs",
        "pgdata",
        "pgdata17",
        # Do not prune every directory named "reports" — docs/reports is public portal content.
        ".vscode-test",
        "visual-baselines",
    }
)

# Written after copy; not part of the source allowlist.
_GENERATED_STAGING_MARKERS = frozenset({".codestrata-export-snapshot.json"})


@dataclass
class FileDelta:
    added: list[str] = field(default_factory=list)
    changed: list[str] = field(default_factory=list)
    deleted: list[str] = field(default_factory=list)
    excluded: list[str] = field(default_factory=list)
    copied: list[str] = field(default_factory=list)


def _load_manifest(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "exports" not in data:
        raise ValueError(f"Invalid manifest: {path}")
    return data


def _match_any(rel: str, patterns: list[str]) -> bool:
    return any(
        fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(Path(rel).name, pat)
        for pat in patterns
    )


def _iter_files(base: Path) -> list[Path]:
    """List files under ``base``, pruning known generated directories early."""

    files: list[Path] = []
    if not base.exists():
        return files
    for dirpath, dirnames, filenames in os.walk(base, topdown=True, followlinks=False):
        dirnames[:] = sorted(
            name
            for name in dirnames
            if name not in _PRUNE_DIR_NAMES and not name.endswith(".egg-info")
        )
        for name in sorted(filenames):
            path = Path(dirpath) / name
            if path.is_file() and not path.is_symlink():
                files.append(path)
    return files


def _rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _should_exclude(rel: str, *, export_exclude: list[str], default_exclude: list[str]) -> bool:
    return _match_any(rel, export_exclude) or _match_any(rel, default_exclude)


def _collect_included(
    source_root: Path,
    include_patterns: list[str],
    *,
    export_exclude: list[str],
    default_exclude: list[str],
) -> tuple[dict[str, Path], list[str]]:
    """Return mapping destination-rel -> source path, plus excluded relative paths."""

    selected: dict[str, Path] = {}
    excluded: list[str] = []
    all_files = _iter_files(source_root)
    for path in all_files:
        rel = _rel(path, source_root)
        if _should_exclude(rel, export_exclude=export_exclude, default_exclude=default_exclude):
            excluded.append(rel)
            continue
        if include_patterns and not _match_any(rel, include_patterns):
            excluded.append(rel)
            continue
        selected[rel] = path
    return selected, sorted(set(excluded))


def export_one(
    *,
    root: Path,
    export: dict[str, Any],
    staging_root: Path,
    default_exclude: list[str],
    dry_run: bool,
) -> FileDelta:
    name = str(export["name"])
    source_root = root / str(export["source_root"])
    dest_root = staging_root / name
    include_patterns = list(export.get("include") or ["**"])
    export_exclude = list(export.get("exclude") or [])

    selected, excluded = _collect_included(
        source_root,
        include_patterns,
        export_exclude=export_exclude,
        default_exclude=default_exclude,
    )

    for extra in export.get("extra_includes") or []:
        src = root / str(extra["from"])
        dest_rel = str(extra["to"]).replace("\\", "/")
        if not src.exists():
            raise FileNotFoundError(f"extra_includes missing: {src}")
        if src.is_dir():
            for path in _iter_files(src):
                rel = f"{dest_rel}/{_rel(path, src)}"
                if _should_exclude(
                    rel, export_exclude=export_exclude, default_exclude=default_exclude
                ):
                    excluded.append(rel)
                    continue
                selected[rel] = path
        else:
            selected[dest_rel] = src

    delta = FileDelta(excluded=sorted(set(excluded)))
    previous: dict[str, str] = {}
    if dest_root.exists():
        for path in _iter_files(dest_root):
            previous[_rel(path, dest_root)] = _sha256(path)

    planned = sorted(selected)
    planned_set = set(planned)
    prev_set = set(previous)

    delta.added = sorted(
        rel
        for rel in (planned_set - prev_set)
        if Path(rel).name not in _GENERATED_STAGING_MARKERS
    )
    delta.deleted = sorted(
        rel
        for rel in (prev_set - planned_set)
        if Path(rel).name not in _GENERATED_STAGING_MARKERS
    )
    delta.changed = sorted(
        rel
        for rel in (planned_set & prev_set)
        if Path(rel).name not in _GENERATED_STAGING_MARKERS
        and _sha256(selected[rel]) != previous[rel]
    )
    delta.copied = planned

    if dry_run:
        return delta

    if dest_root.exists():
        shutil.rmtree(dest_root)
    dest_root.mkdir(parents=True, exist_ok=True)

    for rel in planned:
        src = selected[rel]
        dest = dest_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)

    # Deterministic empty marker for placeholder-only trees
    if not planned and export.get("source_root") in {"cursor-plugin", "vscode-plugin"}:
        (dest_root / ".gitkeep").write_text("", encoding="utf-8")

    return delta


def _print_delta(name: str, delta: FileDelta, *, dry_run: bool) -> None:
    mode = "DRY-RUN" if dry_run else "EXPORT"
    print(f"[{mode}] {name}")
    print(f"  copied={len(delta.copied)} added={len(delta.added)} "
          f"changed={len(delta.changed)} deleted={len(delta.deleted)} "
          f"excluded={len(delta.excluded)}")
    for label, rows in (
        ("added", delta.added[:20]),
        ("changed", delta.changed[:20]),
        ("deleted", delta.deleted[:20]),
    ):
        if not rows:
            continue
        print(f"  {label}:")
        for row in rows:
            print(f"    - {row}")
        remaining = {
            "added": delta.added,
            "changed": delta.changed,
            "deleted": delta.deleted,
        }[label]
        if len(remaining) > 20:
            print(f"    … {len(remaining) - 20} more")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="Path to public-export-manifest.yaml",
    )
    parser.add_argument(
        "--repo",
        action="append",
        dest="repos",
        help="Export only this public repo name (repeatable). Default: all.",
    )
    parser.add_argument(
        "--staging",
        type=Path,
        default=None,
        help="Staging directory (default from manifest).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report planned file operations without writing.",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove staging directory before export.",
    )
    args = parser.parse_args(argv)

    manifest = _load_manifest(args.manifest)
    staging = args.staging or (ROOT / str(manifest.get("staging_directory", ".export-staging")))
    default_exclude = list((manifest.get("defaults") or {}).get("exclude_globs") or [])

    exports = list(manifest["exports"])
    if args.repos:
        wanted = set(args.repos)
        exports = [
            item
            for item in exports
            if item["name"] in wanted or item.get("public_repository") in wanted
        ]
        missing = wanted - {item["name"] for item in exports} - {
            item.get("public_repository") for item in exports
        }
        if missing:
            print(f"Unknown export(s): {sorted(missing)}", file=sys.stderr)
            return 2

    if args.clean and staging.exists() and not args.dry_run:
        shutil.rmtree(staging)

    staging.mkdir(parents=True, exist_ok=True)
    # Ensure scripts/ is importable for extraction snapshot helpers.
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)

    failures = 0
    for export in exports:
        dest_preview = staging / str(export["name"])
        previous_exists = dest_preview.is_dir() and any(dest_preview.iterdir())
        try:
            delta = export_one(
                root=ROOT,
                export=export,
                staging_root=staging,
                default_exclude=default_exclude,
                dry_run=args.dry_run,
            )
        except Exception as error:  # noqa: BLE001 - CLI boundary
            print(f"[ERROR] {export.get('name')}: {error}", file=sys.stderr)
            failures += 1
            continue
        _print_delta(str(export["name"]), delta, dry_run=args.dry_run)
        if not args.dry_run:
            dest = staging / export["name"]
            print(f"  staging: {dest}")
            try:
                from release.extraction import write_export_snapshot

                mode = "update" if previous_exists else "first_time"
                write_export_snapshot(
                    staging_repo=dest,
                    export_name=str(export["name"]),
                    manifest_version=manifest.get("version"),
                    mode=mode,
                )
            except Exception as snapshot_error:  # noqa: BLE001
                print(f"  warning: export snapshot not written: {snapshot_error}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
