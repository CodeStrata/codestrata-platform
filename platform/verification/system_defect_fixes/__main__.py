"""CLI entry: ``python -m verification.system_defect_fixes``."""

from __future__ import annotations

import argparse
from pathlib import Path

from verification.system_defect_fixes.contract import (
    SV13_OUTPUT_RELATIVE,
    VERIFICATION_JSON,
)
from verification.system_defect_fixes.runner import run_system_defect_fixes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="SV.13 Resolve Engineering Intelligence unsafe_metadata defect",
    )
    parser.add_argument("--monorepo-root", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args(argv)

    report = run_system_defect_fixes(
        monorepo=args.monorepo_root,
        output_dir=args.output_dir,
    )
    out = args.output_dir or Path(SV13_OUTPUT_RELATIVE)
    print(f"SV.13 system defect fixes: {report.verdict}")
    print(
        f"repositories={report.repository_count} "
        f"checks_pass={sum(1 for c in report.checks if c.ok)}/"
        f"{len(report.checks)}"
    )
    print(f"report: {out / VERIFICATION_JSON}")
    return 0 if report.verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
