"""Slice 14.3 runner."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from verification.assessment_report_redesign import ASSESSMENT_REPORT_REDESIGN_ID
from verification.assessment_report_redesign.contract import (
    ALLOWED_LIMITATIONS,
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV143_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.assessment_report_redesign.models import (
    AssessmentReportRedesignReport,
    CheckResult,
    Defect,
    Verdict,
)
from verification.assessment_report_redesign.reporting import check_all, release_posture


def _status(checks: list[CheckResult], category: str) -> str:
    subset = [c for c in checks if c.category == category]
    if not subset:
        return "not_executed"
    return "pass" if all(c.ok for c in subset) else "fail"


def _decide(failed: int, defects: list[Defect], limitations: list[str]) -> Verdict:
    if failed or defects:
        return "FAIL"
    if limitations:
        return "PASS_WITH_LIMITATIONS"
    return "PASS"


def build_report(monorepo: Path, tmp_path: Path | None = None) -> AssessmentReportRedesignReport:
    contract = default_contract()
    assert contract.start_slice_14_4 is False
    assert contract.no_eir_redesign is True

    own_tmp = tmp_path is None
    if tmp_path is None:
        tmp_ctx = tempfile.TemporaryDirectory(prefix="sv143-")
        tmp_path = Path(tmp_ctx.__enter__())
    else:
        tmp_ctx = None

    try:
        checks, defects, meta = check_all(monorepo, tmp_path)
    finally:
        if own_tmp and tmp_ctx is not None:
            tmp_ctx.__exit__(None, None, None)

    limitations = sorted(ALLOWED_LIMITATIONS)
    failed = sum(1 for c in checks if not c.ok)
    posture = release_posture()
    if failed or defects:
        posture = {**posture, "slice_14_3_complete": False}

    return AssessmentReportRedesignReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=ASSESSMENT_REPORT_REDESIGN_ID,
        verdict=_decide(failed, defects, limitations),
        design_policy_status=_status(checks, "design_policy"),
        design_system_consumption_status=(
            "pass" if meta.get("design_system_consumed") and _status(checks, "design_system") == "pass"
            else _status(checks, "design_system")
        ),
        schema_boundary_status=_status(checks, "schema_boundary"),
        renderer_status=_status(checks, "renderer"),
        report_shell_status=_status(checks, "report_shell"),
        executive_summary_status=_status(checks, "executive_summary"),
        assessment_head_status=_status(checks, "assessment_head"),
        finding_status=_status(checks, "finding"),
        evidence_status=_status(checks, "evidence"),
        recommendation_status=_status(checks, "recommendation"),
        score_status=_status(checks, "score"),
        risk_status=_status(checks, "risk"),
        navigation_status=_status(checks, "navigation"),
        responsive_status=_status(checks, "responsive"),
        print_status=_status(checks, "print"),
        accessibility_status=_status(checks, "accessibility"),
        offline_status=_status(checks, "offline"),
        determinism_status=_status(checks, "determinism"),
        eir_boundary_status=_status(checks, "eir_boundary"),
        legacy_style_status=_status(checks, "legacy_style"),
        release_posture=posture,
        defects=defects,
        blockers=[],
        limitations=limitations,
        checks=checks,
        total_checks=len(checks),
        failed_checks=failed,
    )


def write_report(monorepo: Path, report: AssessmentReportRedesignReport) -> Path:
    out_dir = monorepo / SV143_OUTPUT_RELATIVE
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / REPORT_JSON
    text = json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n"
    assert "timestamp" not in text
    assert "/Users/" not in text
    assert "file://" not in text
    json_path.write_text(text, encoding="utf-8")
    (out_dir / REPORT_MD).write_text(
        f"# {SCHEMA_NAME}:{SCHEMA_VERSION}\n\n"
        f"Verdict: **{report.verdict}**\n\n"
        f"Checks: {report.total_checks} (failed: {report.failed_checks})\n\n"
        "Slice 14.3 redesigns Assessment HTML presentation on the Design System. "
        "Assessment schema 1.2 and assessment truth unchanged. "
        "Engineering Intelligence Report unchanged. Slice 14.4 not started. "
        "No commit/tag/publish/deploy.\n",
        encoding="utf-8",
    )
    return json_path


def main() -> int:
    monorepo = monorepo_root_from_here()
    report = build_report(monorepo)
    path = write_report(monorepo, report)
    print(
        f"{SCHEMA_NAME}:{SCHEMA_VERSION} verdict={report.verdict} "
        f"checks={report.total_checks} failed={report.failed_checks} "
        f"report={path.name}"
    )
    return 0 if report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
