"""python -m verification.community_assessment_engineering_intelligence"""

from __future__ import annotations

from verification.community_assessment_engineering_intelligence.contract import (
    REPORT_JSON,
    SV1719_OUTPUT_RELATIVE,
    monorepo_root_from_here,
)
from verification.community_assessment_engineering_intelligence.runner import run


def main() -> int:
    root = monorepo_root_from_here()
    report = run(root)
    print(
        f"{report.verdict} checks={report.total_checks} failed={report.failed_checks} "
        f"report={SV1719_OUTPUT_RELATIVE}/{REPORT_JSON}"
    )
    print(
        "start_slice_17_19=true start_slice_17_20=true start_slice_17_21=false "
        f"eir_generated={report.eir_generation.get('generated')} "
        f"repository_count={report.eir_generation.get('repository_count')} "
        f"limitations={len(report.limitations)}"
    )
    return 0 if report.verdict != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
