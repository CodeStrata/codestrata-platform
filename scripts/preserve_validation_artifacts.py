#!/usr/bin/env python3
"""Preserve End-to-End validation assessment artifacts under reports/validation/.

Copies an existing assess run (HTML, JSON, graphs, and sibling artifacts) into:

    reports/validation/<repository-name>/<timestamp>/
    reports/validation/<repository-name>/latest/

Keeps only the newest ``keep`` timestamped runs per repository (default: 3).
Does not change assessment, report generation, graph generation, or Platform APIs.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VALIDATION_ROOT = ROOT / "reports" / "validation"
DEFAULT_KEEP = 3

# Assess CLI run dirs look like 20260728-120723; validation folders use a
# human-readable stamp: 2026-07-28_12-07-23.
_ASSESS_RUN_PATTERN = re.compile(r"^(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})$")
_VALIDATION_RUN_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}$")


def validation_timestamp_from_run_name(run_name: str) -> str:
    """Map an assess run directory name to a validation timestamp folder name."""

    match = _ASSESS_RUN_PATTERN.match(run_name)
    if match:
        year, month, day, hour, minute, second = match.groups()
        return f"{year}-{month}-{day}_{hour}-{minute}-{second}"
    # Fallback: stable unique stamp when source is not an assess-named directory.
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def find_latest_assess_run(search_root: Path) -> Path | None:
    """Find the newest completed assess run under a reports tree."""

    if not search_root.is_dir():
        return None
    candidates: list[Path] = []
    for path in search_root.rglob("report.html"):
        run_dir = path.parent
        if (run_dir / "report.json").is_file():
            candidates.append(run_dir)
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def list_validation_run_directories(repository_root: Path) -> list[Path]:
    """Return timestamped validation run dirs newest-first (excludes ``latest``)."""

    if not repository_root.is_dir():
        return []
    runs = [
        path
        for path in repository_root.iterdir()
        if path.is_dir()
        and not path.is_symlink()
        and path.name != "latest"
        and _VALIDATION_RUN_PATTERN.match(path.name)
    ]
    return sorted(runs, key=lambda path: path.name, reverse=True)


def retain_validation_runs(repository_root: Path, *, keep: int = DEFAULT_KEEP) -> list[Path]:
    """Delete older timestamped validation runs beyond ``keep``."""

    if keep < 1:
        raise ValueError("keep must be at least 1")
    runs = list_validation_run_directories(repository_root)
    deleted: list[Path] = []
    for outdated in runs[keep:]:
        shutil.rmtree(outdated)
        deleted.append(outdated)
    return deleted


def _copy_run_tree(source_run: Path, destination: Path) -> None:
    """Copy assess run contents into destination (replace if present)."""

    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)

    # Prefer full run copy for review; always ensure HTML/JSON/graphs when present.
    for child in source_run.iterdir():
        target = destination / child.name
        if child.is_dir():
            shutil.copytree(child, target)
        elif child.is_file():
            shutil.copy2(child, target)

    required = ("report.html", "report.json")
    missing = [name for name in required if not (destination / name).is_file()]
    if missing:
        raise FileNotFoundError(
            f"Validation copy incomplete; missing {missing} under {destination}"
        )


def preserve_validation_artifacts(
    source_run: Path,
    *,
    repository_name: str | None = None,
    validation_root: Path = DEFAULT_VALIDATION_ROOT,
    keep: int = DEFAULT_KEEP,
) -> Path:
    """Copy ``source_run`` into reports/validation/<repo>/<stamp>/ and refresh latest.

    Returns the timestamped destination directory.
    """

    source_run = source_run.expanduser().resolve()
    if not source_run.is_dir():
        raise FileNotFoundError(f"Assess run directory not found: {source_run}")
    if not (source_run / "report.html").is_file():
        raise FileNotFoundError(f"report.html missing in {source_run}")

    repo = (repository_name or source_run.parent.name).strip()
    if not repo or repo in {".", ".."}:
        raise ValueError("repository_name is required")

    stamp = validation_timestamp_from_run_name(source_run.name)
    repo_root = validation_root / repo
    stamped = repo_root / stamp
    latest = repo_root / "latest"

    _copy_run_tree(source_run, stamped)
    _copy_run_tree(source_run, latest)
    deleted = retain_validation_runs(repo_root, keep=keep)

    print(f"Preserved validation run: {stamped.relative_to(ROOT)}")
    print(f"Updated latest:           {latest.relative_to(ROOT)}")
    if deleted:
        print(
            "Pruned older runs:        "
            + ", ".join(path.name for path in deleted)
        )
    print(
        "Note: graph generation and Platform upload behavior are unchanged; "
        "this script only copies local assess artifacts for review."
    )
    return stamped


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Copy an assess run into reports/validation/<repo>/ "
            "(timestamped + latest; keep 3 runs)."
        )
    )
    parser.add_argument(
        "--source",
        type=Path,
        help="Path to an assess run directory containing report.html",
    )
    parser.add_argument(
        "--from-reports",
        type=Path,
        help="Search this reports tree for the newest assess run",
    )
    parser.add_argument(
        "--repository-name",
        help="Override repository folder name (default: parent of source run)",
    )
    parser.add_argument(
        "--validation-root",
        type=Path,
        default=DEFAULT_VALIDATION_ROOT,
        help=f"Validation root (default: {DEFAULT_VALIDATION_ROOT})",
    )
    parser.add_argument(
        "--keep",
        type=int,
        default=DEFAULT_KEEP,
        help=f"Timestamped runs to retain per repository (default: {DEFAULT_KEEP})",
    )
    args = parser.parse_args(argv)

    source = args.source
    if source is None and args.from_reports is not None:
        source = find_latest_assess_run(args.from_reports.expanduser().resolve())
        if source is None:
            print(
                f"Error: no assess run with report.html found under {args.from_reports}",
                file=sys.stderr,
            )
            return 1
    if source is None:
        parser.error("Provide --source RUN_DIR or --from-reports REPORTS_DIR")

    try:
        preserve_validation_artifacts(
            source,
            repository_name=args.repository_name,
            validation_root=args.validation_root.expanduser().resolve(),
            keep=args.keep,
        )
    except (OSError, ValueError, FileNotFoundError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
