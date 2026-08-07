"""python -m verification.cursor_documentation_removal"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from verification.cursor_documentation_removal.contract import SV123_OUTPUT_RELATIVE
from verification.cursor_documentation_removal.runner import (
    run_cursor_documentation_removal_verification,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Slice 12.3 Cursor documentation removal")
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args(argv)
    report = run_cursor_documentation_removal_verification(
        output_dir=Path(args.output_dir) if args.output_dir else None,
    )
    print(f"verdict={report.verdict}")
    print(f"checks={report.total_checks - report.failed_checks}/{report.total_checks}")
    print(f"output={SV123_OUTPUT_RELATIVE}/cursor-documentation-removal-verification.json")
    return 0 if report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"} else 1


if __name__ == "__main__":
    sys.exit(main())
