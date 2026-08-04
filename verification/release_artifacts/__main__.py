"""CLI entry: ``python -m verification.release_artifacts``."""

from __future__ import annotations

import argparse
from pathlib import Path

from verification.release_artifacts.contract import REPORT_JSON, SV16_OUTPUT_RELATIVE
from verification.release_artifacts.runner import run_release_artifacts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="SV.16 Release Artifact Verification",
    )
    parser.add_argument("--monorepo-root", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--skip-build", action="store_true")
    parser.add_argument("--skip-install", action="store_true")
    args = parser.parse_args(argv)

    report = run_release_artifacts(
        monorepo=args.monorepo_root,
        output_dir=args.output_dir,
        skip_build=args.skip_build,
        skip_install=args.skip_install,
    )
    out = args.output_dir or Path(SV16_OUTPUT_RELATIVE)
    print(f"SV.16 release artifacts: {report.verdict}")
    print(
        f"intended={report.intended_release_version} "
        f"checks_pass={sum(1 for c in report.checks if c.ok)}/{len(report.checks)} "
        f"defects={len(report.defects)} blockers={len(report.blockers)} "
        f"warnings={len(report.warnings)}"
    )
    print(f"report: {out / REPORT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
