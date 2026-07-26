#!/usr/bin/env python3
"""Export public mirror repositories from codestrata-platform (staging only).

Does not create, push, or publish GitHub repositories.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
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
    files: list[Path] = []
    if not base.exists():
        return files
    for path in sorted(base.rglob("*")):
        if path.is_file():
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

    delta.added = sorted(planned_set - prev_set)
    delta.deleted = sorted(prev_set - planned_set)
    delta.changed = sorted(
        rel
        for rel in (planned_set & prev_set)
        if _sha256(selected[rel]) != previous[rel]
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
    failures = 0
    for export in exports:
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
            print(f"  staging: {staging / export['name']}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
