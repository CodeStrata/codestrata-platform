"""CLI entry: ``python -m verification.engineering_intelligence``."""

from __future__ import annotations

import argparse
from pathlib import Path

from verification.engineering_intelligence.contract import PREFERRED_FIVE_LANGUAGE_SUBSET
from verification.engineering_intelligence.runner import (
    run_engineering_intelligence_verification,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="SV.6 Engineering Intelligence Pipeline Verification",
    )
    parser.add_argument("--monorepo", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=None,
        help="Directory of cached schema-1.2 assessment report.json inputs",
    )
    parser.add_argument(
        "--repository",
        action="append",
        default=None,
        help="Catalog repository id (repeatable). Default: preferred five-language subset.",
    )
    parser.add_argument(
        "--with-catalog-network",
        action="store_true",
        help="Clone qualified pinned SHAs and run canonical offline assess as needed",
    )
    parser.add_argument(
        "--offline-scenarios-only",
        action="store_true",
        help="Run synthetic offline scenarios only (no catalog assessments)",
    )
    args = parser.parse_args(argv)

    repository_ids = tuple(args.repository) if args.repository else PREFERRED_FIVE_LANGUAGE_SUBSET
    report = run_engineering_intelligence_verification(
        monorepo=args.monorepo,
        output_dir=args.output_dir,
        cache_dir=args.cache_dir,
        repository_ids=repository_ids,
        with_catalog_network=args.with_catalog_network,
        offline_scenarios_only=args.offline_scenarios_only,
    )
    print(
        f"SV.6 engineering intelligence verification: "
        f"{'PASS' if report.ok else 'FAIL'}"
    )
    print(f"verdict: {report.verdict}")
    if report.defects:
        print(f"defects: {', '.join(report.defects[:8])}")
    out = (
        (args.output_dir or Path("platform/reports/verification"))
        / "engineering-intelligence-verification.json"
    )
    print(f"report: {out}")
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
