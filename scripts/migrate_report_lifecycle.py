#!/usr/bin/env python3
"""Migrate assessment/EIR artifacts to logical current/previous (Slice 17.15).

Usage (from workspace root):

  python scripts/migrate_report_lifecycle.py
  python scripts/migrate_report_lifecycle.py --dry-run

Does not upload anything. Does not touch validation/suites/.
Does not purge Data Lake / telemetry history.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE_SRC = ROOT / "engine" / "src"
if ENGINE_SRC.is_dir():
    sys.path.insert(0, str(ENGINE_SRC))

from codestrata.artifacts.lifecycle_migration import migrate_report_lifecycle  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path.cwd(),
        help="Workspace root containing .codestrata-artifacts/",
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        default=None,
        help="Optional repository catalog.json for GitHub owner/repo mapping",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    catalog = args.catalog
    if catalog is None:
        candidate = ROOT / "validation" / "repository-catalog" / "catalog.json"
        if candidate.is_file():
            catalog = candidate
    payload = migrate_report_lifecycle(
        workspace=args.workspace.resolve(),
        catalog_path=catalog,
        dry_run=args.dry_run,
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 1 if payload.get("errors") else 0


if __name__ == "__main__":
    raise SystemExit(main())
