"""CLI entry: python -m verification.product_cleanup_repository_split_completion"""

from __future__ import annotations

import argparse
import sys

from verification.product_cleanup_repository_split_completion.runner import run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Slice 12.10 Epic 12 completion verification"
    )
    parser.add_argument(
        "--skip-expensive",
        action="store_true",
        help="Consume Slice 12.7 report instead of re-running dual export/OpenTofu",
    )
    parser.add_argument(
        "--skip-vscode-npm",
        action="store_true",
        help="Skip VS Code npm compile/test/package:dry",
    )
    args = parser.parse_args(argv)
    report = run(
        rerun_expensive=not args.skip_expensive,
        run_vscode_npm=not args.skip_vscode_npm,
    )
    print(
        f"{report.schema_name}:{report.schema_version} "
        f"verdict={report.verdict} "
        f"slices={report.completed_slices}/{report.total_slices} "
        f"checks={report.total_checks} failed={report.failed_checks} "
        f"start_epic_13={report.start_epic_13}"
    )
    if report.failed_checks > 0 or report.verdict == "FAIL":
        for c in report.checks:
            if not c.ok:
                print(f"  FAIL {c.name}: {c.detail}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
