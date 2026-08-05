"""CLI entry: ``python -m verification.community_data_lake``."""

from __future__ import annotations

import argparse
from pathlib import Path

from verification.community_data_lake.runner import run_community_data_lake_verification


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="SV.9 Community Data Lake Integration Verification",
    )
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument(
        "--skip-opentofu",
        action="store_true",
        help="Skip OpenTofu CLI validation (faster; not for release runs)",
    )
    args = parser.parse_args(argv)

    report = run_community_data_lake_verification(
        output_dir=args.output_dir,
        run_opentofu=not args.skip_opentofu,
    )
    print(
        f"SV.9 community data lake verification: "
        f"{'PASS' if report.ok else 'FAIL'}"
    )
    print(f"verdict: {report.verdict}")
    if report.defects:
        print(f"defects: {', '.join(report.defects[:8])}")
    out = (
        (args.output_dir or Path("platform/reports/verification"))
        / "community-data-lake-verification.json"
    )
    print(f"report: {out}")
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
