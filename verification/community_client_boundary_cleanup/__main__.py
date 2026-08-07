"""python -m verification.community_client_boundary_cleanup"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from verification.community_client_boundary_cleanup.contract import SV124_OUTPUT_RELATIVE
from verification.community_client_boundary_cleanup.runner import (
    run_community_client_boundary_cleanup_verification,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Slice 12.4 Community client boundary cleanup")
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args(argv)
    report = run_community_client_boundary_cleanup_verification(
        output_dir=Path(args.output_dir) if args.output_dir else None,
    )
    print(f"verdict={report.verdict}")
    print(f"checks={report.total_checks - report.failed_checks}/{report.total_checks}")
    print(
        f"output={SV124_OUTPUT_RELATIVE}/community-client-boundary-cleanup-verification.json"
    )
    return 0 if report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"} else 1


if __name__ == "__main__":
    sys.exit(main())
