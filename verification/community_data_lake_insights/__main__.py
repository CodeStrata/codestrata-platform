"""python -m verification.community_data_lake_insights"""

from __future__ import annotations

from verification.community_data_lake_insights.contract import (
    REPORT_JSON,
    SV1718_OUTPUT_RELATIVE,
    monorepo_root_from_here,
)
from verification.community_data_lake_insights.runner import run


def main() -> int:
    root = monorepo_root_from_here()
    report = run(root)
    print(
        f"{report.verdict} checks={report.total_checks} failed={report.failed_checks} "
        f"report={SV1718_OUTPUT_RELATIVE}/{REPORT_JSON}"
    )
    print(
        "start_slice_17_18=true start_slice_17_19=true start_slice_17_20=false "
        f"live_probe_completed={report.live_probe.get('live_probe_completed')} "
        f"transport={report.transport.get('production_http_transport_available_after_opt_in')} "
        f"limitations={len(report.limitations)}"
    )
    return 0 if report.verdict != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
