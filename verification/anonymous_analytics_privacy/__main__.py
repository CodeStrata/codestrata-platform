"""CLI entry: ``python -m verification.anonymous_analytics_privacy``."""

from __future__ import annotations

import argparse
from pathlib import Path

from verification.anonymous_analytics_privacy.contract import REPORT_JSON, SV108_OUTPUT_RELATIVE
from verification.anonymous_analytics_privacy.runner import (
    run_anonymous_analytics_privacy_verification,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Slice 10.8 Anonymous Analytics Privacy Verification",
    )
    parser.add_argument("--monorepo-root", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args(argv)

    report = run_anonymous_analytics_privacy_verification(
        monorepo=args.monorepo_root,
        output_dir=args.output_dir,
        write_report=not args.no_write,
    )
    out = args.output_dir or Path(SV108_OUTPUT_RELATIVE)
    print(f"SV10.8 anonymous analytics privacy: {report.verdict}")
    print(
        f"checks_pass={report.total_checks - report.failed_checks}/"
        f"{report.total_checks} defects={len(report.defects)}"
    )
    if not args.no_write:
        print(f"report: {out / REPORT_JSON}")
    return 0 if report.verdict in {"pass", "pass_with_limitations"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
