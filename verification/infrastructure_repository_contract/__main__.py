"""python -m verification.infrastructure_repository_contract"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from verification.infrastructure_repository_contract.contract import (
    REPORT_JSON,
    SV125_OUTPUT_RELATIVE,
)
from verification.infrastructure_repository_contract.runner import (
    run_infrastructure_repository_contract_verification,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Slice 12.5 Infrastructure repository contract verification"
    )
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args(argv)
    report = run_infrastructure_repository_contract_verification(
        output_dir=Path(args.output_dir) if args.output_dir else None,
    )
    print(f"verdict={report.verdict}")
    print(f"checks={report.total_checks - report.failed_checks}/{report.total_checks}")
    print(f"output={SV125_OUTPUT_RELATIVE}/{REPORT_JSON}")
    return 0 if report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"} else 1


if __name__ == "__main__":
    sys.exit(main())
