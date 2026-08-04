"""CLI entry: ``python -m verification.cross_schema_compatibility``."""

from __future__ import annotations

import argparse
from pathlib import Path

from verification.cross_schema_compatibility.contract import (
    REPORT_JSON,
    SV14_OUTPUT_RELATIVE,
)
from verification.cross_schema_compatibility.runner import run_cross_schema_compatibility


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="SV.14 Cross-Schema Compatibility Verification",
    )
    parser.add_argument("--monorepo-root", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args(argv)

    report = run_cross_schema_compatibility(
        monorepo=args.monorepo_root,
        output_dir=args.output_dir,
    )
    out = args.output_dir or Path(SV14_OUTPUT_RELATIVE)
    print(f"SV.14 cross-schema compatibility: {report.verdict}")
    print(
        f"repositories={report.repository_count} "
        f"checks_pass={sum(1 for c in report.checks if c.ok)}/{len(report.checks)} "
        f"failures={len(report.compatibility_failures)} "
        f"warnings={len(report.warnings)}"
    )
    print(f"report: {out / REPORT_JSON}")
    return 0 if report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
