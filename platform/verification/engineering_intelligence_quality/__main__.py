"""CLI entry: ``python -m verification.engineering_intelligence_quality``."""

from __future__ import annotations

import argparse
from pathlib import Path

from verification.engineering_intelligence_quality.contract import (
    REVIEW_JSON,
    SV12_OUTPUT_RELATIVE,
)
from verification.engineering_intelligence_quality.runner import (
    run_engineering_intelligence_quality,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="SV.12 Engineering Intelligence Quality Review (22 curated repos)",
    )
    parser.add_argument("--monorepo-root", type=Path, default=None)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Defaults to platform/reports/verification/sv12 (never platform/demo)",
    )
    args = parser.parse_args(argv)

    report = run_engineering_intelligence_quality(
        monorepo=args.monorepo_root,
        output_dir=args.output_dir,
    )
    out = args.output_dir or Path(SV12_OUTPUT_RELATIVE)
    print(f"SV.12 engineering intelligence quality: {report.verdict}")
    print(
        f"repositories={report.repository_count} "
        f"defects={len(report.defect_candidates)} "
        f"observations={len(report.editorial_observations)}"
    )
    print(f"report: {out / REVIEW_JSON}")
    return 0 if report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
