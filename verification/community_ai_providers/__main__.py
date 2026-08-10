"""python -m verification.community_ai_providers"""

from __future__ import annotations

from verification.community_ai_providers.contract import (
    REPORT_JSON,
    SV1720_OUTPUT_RELATIVE,
    monorepo_root_from_here,
)
from verification.community_ai_providers.runner import run


def main() -> int:
    root = monorepo_root_from_here()
    report = run(root)
    print(
        f"{report.verdict} checks={report.total_checks} failed={report.failed_checks} "
        f"report={SV1720_OUTPUT_RELATIVE}/{REPORT_JSON}"
    )
    print(
        "start_slice_17_20=true start_slice_17_21=true start_slice_17_22=false "
        f"openai={report.openai.get('e2e_status')} "
        f"bedrock={report.bedrock.get('e2e_status')} "
        f"openrouter={report.openrouter.get('e2e_status')} "
        f"limitations={len(report.limitations)}"
    )
    return 0 if report.verdict != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
