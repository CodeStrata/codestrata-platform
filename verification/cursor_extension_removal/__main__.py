"""python -m verification.cursor_extension_removal"""

from __future__ import annotations

import argparse
import sys

from verification.cursor_extension_removal.contract import SV121_OUTPUT_RELATIVE
from verification.cursor_extension_removal.runner import run_cursor_extension_removal_verification


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Slice 12.1 Cursor extension removal verification")
    parser.add_argument("--skip-vscode-compile", action="store_true")
    parser.add_argument("--skip-vscode-tests", action="store_true")
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args(argv)

    report = run_cursor_extension_removal_verification(
        output_dir=None if not args.output_dir else __import__("pathlib").Path(args.output_dir),
        run_vscode_compile=not args.skip_vscode_compile,
        run_vscode_tests=not args.skip_vscode_tests,
    )
    print(f"verdict={report.verdict}")
    print(f"checks={report.total_checks - report.failed_checks}/{report.total_checks}")
    print(f"output={SV121_OUTPUT_RELATIVE}/cursor-extension-removal-verification.json")
    return 0 if report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"} else 1


if __name__ == "__main__":
    sys.exit(main())
