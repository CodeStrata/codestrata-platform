#!/usr/bin/env python3
"""Migrate legacy reports/ trees into .codestrata-artifacts/ (Slice 17.12).

Usage (from monorepo or customer workspace root):

  python scripts/migrate_codestrata_artifacts.py
  python scripts/migrate_codestrata_artifacts.py --move

Does not upload anything. Does not delete legacy trees unless --move.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Prefer installed package; fall back to engine src for monorepo.
ROOT = Path(__file__).resolve().parents[1]
ENGINE_SRC = ROOT / "engine" / "src"
if ENGINE_SRC.is_dir():
    sys.path.insert(0, str(ENGINE_SRC))

from codestrata.artifacts.migration import (  # noqa: E402
    migrate_legacy_report_tree,
    migrate_legacy_verification_tree,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path.cwd(),
        help="Workspace root containing reports/ and/or .codestrata-artifacts/",
    )
    parser.add_argument(
        "--move",
        action="store_true",
        help="Move files instead of copying (default: copy).",
    )
    args = parser.parse_args()
    copy = not args.move
    assessments = migrate_legacy_report_tree(workspace=args.workspace, copy=copy)
    verification = migrate_legacy_verification_tree(workspace=args.workspace, copy=copy)
    payload = {
        "assessments_migrated": assessments.migrated_runs,
        "assessments_skipped": assessments.skipped,
        "assessments_errors": assessments.errors,
        "verification_migrated": verification.migrated_runs,
        "verification_skipped": verification.skipped,
        "verification_errors": verification.errors,
        "mode": "move" if args.move else "copy",
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 1 if assessments.errors or verification.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
