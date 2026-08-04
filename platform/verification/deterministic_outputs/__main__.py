"""CLI entry: ``python -m verification.deterministic_outputs``."""

from __future__ import annotations

import argparse
from pathlib import Path

from verification.deterministic_outputs.contract import (
    REPORT_JSON,
    SV15_OUTPUT_RELATIVE,
)
from verification.deterministic_outputs.runner import run_deterministic_outputs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="SV.15 Deterministic Output Verification",
    )
    parser.add_argument("--monorepo-root", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args(argv)

    report = run_deterministic_outputs(
        monorepo=args.monorepo_root,
        output_dir=args.output_dir,
    )
    out = args.output_dir or Path(SV15_OUTPUT_RELATIVE)
    print(f"SV.15 deterministic outputs: {report.verdict}")
    print(
        f"repositories={report.repository_count} "
        f"checks_pass={sum(1 for c in report.checks if c.ok)}/{len(report.checks)} "
        f"defects={len(report.defects)} warnings={len(report.warnings)}"
    )
    print(f"report: {out / REPORT_JSON}")
    return 0 if report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
