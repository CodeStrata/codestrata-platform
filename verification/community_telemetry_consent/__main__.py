"""python -m verification.community_telemetry_consent"""

from __future__ import annotations

from verification.community_telemetry_consent.contract import (
    REPORT_JSON,
    SV1717_OUTPUT_RELATIVE,
    monorepo_root_from_here,
)
from verification.community_telemetry_consent.runner import run


def main() -> int:
    root = monorepo_root_from_here()
    report = run(root)
    print(
        f"{report.verdict} checks={report.total_checks} failed={report.failed_checks} "
        f"report={SV1717_OUTPUT_RELATIVE}/{REPORT_JSON}"
    )
    print(
        f"start_slice_17_17=true start_slice_17_18=true start_slice_17_19=false "
        f"limitations={len(report.limitations)}"
    )
    return 0 if report.verdict != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
