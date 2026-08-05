"""CLI entry: ``python -m verification.community_data_lake_completion``."""

from __future__ import annotations

import argparse
from pathlib import Path

from verification.community_data_lake_completion.reporting import REPORT_FILENAME
from verification.community_data_lake_completion.runner import (
    run_community_data_lake_completion_verification,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Slice 8.15 Community Data Lake Completion Verification",
    )
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument(
        "--skip-opentofu",
        action="store_true",
        help="Skip OpenTofu CLI validation (faster; not for release runs)",
    )
    parser.add_argument(
        "--skip-integration",
        action="store_true",
        help="Reuse existing SV.9 report instead of re-running integration suite",
    )
    args = parser.parse_args(argv)

    report = run_community_data_lake_completion_verification(
        output_dir=args.output_dir,
        run_opentofu=not args.skip_opentofu,
        run_integration=not args.skip_integration,
    )
    print(
        "Slice 8.15 community data lake completion verification: "
        f"{'PASS' if report.ok else 'FAIL'}"
    )
    print(f"verdict: {report.verdict}")
    if report.defects:
        print(f"defects: {', '.join(report.defects[:8])}")
    out = (args.output_dir or Path("platform/reports/verification")) / REPORT_FILENAME
    print(f"report: {out}")
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
