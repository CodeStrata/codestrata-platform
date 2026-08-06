"""CLI entry: ``python -m verification.privacy_first_telemetry_completion``."""

from __future__ import annotations

import argparse
from pathlib import Path

from verification.privacy_first_telemetry_completion.contract import (
    REPORT_JSON,
    SV915_OUTPUT_RELATIVE,
)
from verification.privacy_first_telemetry_completion.runner import (
    run_privacy_first_telemetry_completion,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Slice 9.15 Epic 9 Privacy-First Telemetry Completion Verification",
    )
    parser.add_argument("--monorepo-root", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--no-write", action="store_true")
    parser.add_argument("--skip-cross-client", action="store_true")
    args = parser.parse_args(argv)

    report = run_privacy_first_telemetry_completion(
        monorepo=args.monorepo_root,
        output_dir=args.output_dir,
        write_report=not args.no_write,
        run_cross_client_live=not args.skip_cross_client,
    )
    out = args.output_dir or Path(SV915_OUTPUT_RELATIVE)
    print(f"SV9.15 Epic 9 completion: {report.verdict}")
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
