"""CLI entry: ``python -m verification.privacy_first_telemetry``."""

from __future__ import annotations

import argparse
from pathlib import Path

from verification.privacy_first_telemetry.contract import REPORT_JSON, SV914_OUTPUT_RELATIVE
from verification.privacy_first_telemetry.runner import (
    run_cross_client_telemetry_privacy_verification,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Slice 9.14 Cross-Client Telemetry Privacy Verification",
    )
    parser.add_argument("--monorepo-root", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args(argv)

    report = run_cross_client_telemetry_privacy_verification(
        monorepo=args.monorepo_root,
        output_dir=args.output_dir,
        write_report=not args.no_write,
    )
    out = args.output_dir or Path(SV914_OUTPUT_RELATIVE)
    print(f"SV9.14 cross-client telemetry privacy: {report.verdict}")
    print(
        f"checks_pass={report.total_checks - report.failed_checks}/"
        f"{report.total_checks} defects={len(report.defects)}"
    )
    if not args.no_write:
        print(f"report: {out / REPORT_JSON}")
    return 0 if report.verdict in {"pass", "pass_with_limitations"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
