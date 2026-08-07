"""python -m verification.cursor_release_surface_removal"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from verification.cursor_release_surface_removal.contract import SV122_OUTPUT_RELATIVE
from verification.cursor_release_surface_removal.runner import (
    run_cursor_release_surface_removal_verification,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Slice 12.2 Cursor release-surface removal verification"
    )
    parser.add_argument("--skip-vscode-compile", action="store_true")
    parser.add_argument("--skip-vscode-tests", action="store_true")
    parser.add_argument("--skip-vscode-package", action="store_true")
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args(argv)

    report = run_cursor_release_surface_removal_verification(
        output_dir=Path(args.output_dir) if args.output_dir else None,
        run_vscode_compile=not args.skip_vscode_compile,
        run_vscode_tests=not args.skip_vscode_tests,
        run_vscode_package=not args.skip_vscode_package,
    )
    print(f"verdict={report.verdict}")
    print(f"checks={report.total_checks - report.failed_checks}/{report.total_checks}")
    print(f"output={SV122_OUTPUT_RELATIVE}/{report.schema_name}.json")
    return 0 if report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"} else 1


if __name__ == "__main__":
    sys.exit(main())
