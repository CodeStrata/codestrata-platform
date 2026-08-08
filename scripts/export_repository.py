#!/usr/bin/env python3
"""Authoritative repository export router (Slice 12.8 / 15.8).

Supports exactly one target per invocation:

  python scripts/export_repository.py \\
    --target community \\
    --destination <community-export-root> \\
    --dry-run

  python scripts/export_repository.py \\
    --target infrastructure \\
    --destination <infrastructure-repository-directory> \\
    --dry-run

  python scripts/export_repository.py \\
    --target insights \\
    --destination <insights-repository-directory> \\
    --dry-run

Community destination is a staging root that may contain multiple public/private
mirror repositories. Infrastructure destination is a single private repository
directory (Approach A). Insights destination is a single private internal
application repository (codestrata-insights).

Does not: merge target policies, create remotes, git commit/push/tag, AWS calls,
OpenTofu plan/apply/destroy, or publish/deploy.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from repository_export_router.errors import RouterError  # noqa: E402
from repository_export_router.models import dumps_result  # noqa: E402
from repository_export_router.router import export_repository, print_human_summary  # noqa: E402
from repository_export_router.targets import SUPPORTED_TARGETS  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Export one repository target (community | infrastructure | insights). "
            "No default target. No Git/AWS/deploy."
        )
    )
    parser.add_argument(
        "--target",
        required=True,
        choices=[t.value for t in SUPPORTED_TARGETS],
        help="Export target (required; closed set)",
    )
    parser.add_argument(
        "--destination",
        required=True,
        type=Path,
        help=(
            "Destination path (required). Community: staging root for multiple "
            "mirror repos. Infrastructure: single private repository directory. "
            "Insights: single private codestrata-insights application directory."
        ),
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
    try:
        result = export_repository(
            target=args.target,
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
