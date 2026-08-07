#!/usr/bin/env python3
"""Compatibility wrapper for Infrastructure export (Slice 12.8).

Authoritative command:

  python scripts/export_repository.py --target infrastructure --destination <path> [--dry-run]

This wrapper preserves the Slice 12.6 CLI and delegates to the target router.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from repository_export_router.errors import RouterError  # noqa: E402
from repository_export_router.models import dumps_result  # noqa: E402
from repository_export_router.router import export_repository, print_human_summary  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compatibility wrapper: export private codestrata-infrastructure. "
            "Prefer: python scripts/export_repository.py --target infrastructure ..."
        )
    )
    parser.add_argument(
        "--destination",
        required=True,
        type=Path,
        help="Caller-provided local destination directory (outside the monorepo)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and plan only; write nothing",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable diagnostics JSON (no absolute paths)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    print(
        "note: compatibility wrapper; authoritative command is "
        "scripts/export_repository.py --target infrastructure",
        file=sys.stderr,
    )
    try:
        result = export_repository(
            target="infrastructure",
            destination=args.destination,
            dry_run=args.dry_run,
        )
    except RouterError as exc:
        print(f"error: {exc.category}", file=sys.stderr)
        return 2

    if args.json:
        sys.stdout.write(dumps_result(result))
    else:
        print_human_summary(result)
    return 0 if result.status == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
