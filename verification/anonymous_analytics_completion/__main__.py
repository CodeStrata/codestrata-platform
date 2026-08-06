"""CLI entry: ``python -m verification.anonymous_analytics_completion``."""

from __future__ import annotations

import argparse
from pathlib import Path

from verification.anonymous_analytics_completion.contract import (
    REPORT_JSON,
    SV109_OUTPUT_RELATIVE,
)
from verification.anonymous_analytics_completion.runner import (
    run_anonymous_analytics_completion,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Slice 10.9 Epic 10 Anonymous Analytics Completion Verification",
    )
    parser.add_argument("--monorepo-root", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--no-write", action="store_true")
    parser.add_argument("--skip-privacy-rerun", action="store_true")
    args = parser.parse_args(argv)

    report = run_anonymous_analytics_completion(
        monorepo=args.monorepo_root,
        output_dir=args.output_dir,
        write_report=not args.no_write,
        rerun_privacy_live=not args.skip_privacy_rerun,
    )
    out = args.output_dir or Path(SV109_OUTPUT_RELATIVE)
    print(f"SV10.9 Epic 10 completion: {report.verdict}")
    print(
        f"slices={report.completed_slice_count}/{report.expected_slice_count} "
        f"checks_pass={report.total_checks - report.failed_checks}/"
        f"{report.total_checks} defects={len(report.defects)} "
        f"blockers={len(report.blockers)}"
    )
    if not args.no_write:
        print(f"report: {out / REPORT_JSON}")
    return 0 if report.verdict in {"pass", "pass_with_limitations"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
