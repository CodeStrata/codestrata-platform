"""CLI entry: ``python -m verification.website_export``."""

from __future__ import annotations

import argparse
from pathlib import Path

from verification.website_export.runner import run_website_export_verification


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="SV.8 Website-Safe Engineering Intelligence Export Verification",
    )
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--cache-dir", type=Path, default=None)
    parser.add_argument(
        "--with-catalog-network",
        action="store_true",
        help="Allow SV.6 assessment cache refresh via network (default: offline cache).",
    )
    args = parser.parse_args(argv)

    report = run_website_export_verification(
        output_dir=args.output_dir,
        cache_dir=args.cache_dir,
        with_catalog_network=args.with_catalog_network,
    )
    print(
        f"SV.8 website export verification: {'PASS' if report.ok else 'FAIL'}"
    )
    print(f"verdict: {report.verdict}")
    if report.defects:
        print(f"defects: {', '.join(report.defects[:8])}")
    out = (
        (args.output_dir or Path("platform/reports/verification"))
        / "website-export-verification.json"
    )
    print(f"report: {out}")
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
