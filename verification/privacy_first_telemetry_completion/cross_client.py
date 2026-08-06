"""Cross-client (Slice 9.14) consumption for completion."""

from __future__ import annotations

import json
from pathlib import Path

from verification.privacy_first_telemetry.contract import (
    REPORT_JSON as CROSS_CLIENT_REPORT_JSON,
    SCHEMA_NAME as CROSS_CLIENT_SCHEMA,
    SV914_OUTPUT_RELATIVE,
)
from verification.privacy_first_telemetry.runner import (
    run_cross_client_telemetry_privacy_verification,
)
from verification.privacy_first_telemetry_completion.models import CheckResult, Defect


def check_cross_client(
    monorepo: Path,
    *,
    run_live: bool = True,
) -> tuple[str, list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    if run_live:
        report = run_cross_client_telemetry_privacy_verification(
            monorepo=monorepo,
            output_dir=monorepo / SV914_OUTPUT_RELATIVE,
            write_report=True,
        )
        ok = report.verdict == "pass" and report.failed_checks == 0
        checks.append(
            CheckResult(
                name="cross_client_live_pass",
                ok=ok,
                detail=f"verdict={report.verdict} failed={report.failed_checks}",
                category="cross_client",
            )
        )
        if not ok:
            defects.append(
                Defect(
                    classification="missing slice evidence",
                    component="9.14",
                    expected="pass",
                    actual=report.verdict,
                )
            )
        status = "pass" if ok else "fail"
    else:
        status = "unknown"

    report_path = monorepo / SV914_OUTPUT_RELATIVE / CROSS_CLIENT_REPORT_JSON
    checks.append(
        CheckResult(
            name="cross_client_report_present",
            ok=report_path.is_file(),
            detail=CROSS_CLIENT_REPORT_JSON,
            category="cross_client",
        )
    )
    if report_path.is_file():
        payload = json.loads(report_path.read_text(encoding="utf-8"))
        checks.append(
            CheckResult(
                name="cross_client_report_schema",
                ok=payload.get("schema_name") == CROSS_CLIENT_SCHEMA
                and payload.get("schema_version") == "1.0.0",
                detail=f"{payload.get('schema_name')}@{payload.get('schema_version')}",
                category="cross_client",
            )
        )
        checks.append(
            CheckResult(
                name="cross_client_report_verdict_pass",
                ok=payload.get("verdict") == "pass",
                detail=str(payload.get("verdict")),
                category="cross_client",
            )
        )
        if payload.get("verdict") != "pass":
            defects.append(
                Defect(
                    classification="missing slice evidence",
                    component="9.14",
                    expected="pass",
                    actual=str(payload.get("verdict")),
                )
            )
            status = "fail"
        elif status != "fail":
            status = "pass"

    for check in checks:
        if not check.ok and not any(d.actual == check.name for d in defects):
            defects.append(
                Defect(
                    classification="missing slice evidence",
                    component="cross_client",
                    expected="pass",
                    actual=check.name,
                    detail=check.detail,
                )
            )
    return status, checks, defects
