"""CLI entry: ``python -m verification.community_cloud_api``."""

from __future__ import annotations

import argparse
from pathlib import Path

from verification.community_cloud_api.runner import run_community_cloud_api_verification


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="SV.7 Community Cloud API End-to-End Verification",
    )
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args(argv)

    report = run_community_cloud_api_verification(output_dir=args.output_dir)
    print(
        f"SV.7 community cloud API verification: "
        f"{'PASS' if report.ok else 'FAIL'}"
    )
    print(f"verdict: {report.verdict}")
    if report.defects:
        print(f"defects: {', '.join(report.defects[:8])}")
    out = (
        (args.output_dir or Path("platform/reports/verification"))
        / "community-cloud-api-verification.json"
    )
    print(f"report: {out}")
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
