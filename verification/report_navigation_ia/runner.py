"""Slice 14.9 runner."""

from __future__ import annotations

import json
from pathlib import Path

from verification.report_navigation_ia import REPORT_IA_ID
from verification.report_navigation_ia.checks import check_all
from verification.report_navigation_ia.contract import (
    ALLOWED_LIMITATIONS,
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV149_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.report_navigation_ia.models import (
    CheckResult,
    Defect,
    ReportNavigationIaReport,
    Verdict,
)


def _status(checks: list[CheckResult], category: str) -> str:
    subset = [check for check in checks if check.category == category]
    if not subset:
        return "not_executed"
    return "pass" if all(check.ok for check in subset) else "fail"


def _decide(failed: int, defects: list[Defect], limitations: list[str]) -> Verdict:
    if failed or defects:
        return "FAIL"
    if limitations:
        return "PASS_WITH_LIMITATIONS"
    return "PASS"


def release_posture() -> dict[str, bool]:
    return {
        "assessment_schema_1_2": True,
        "design_system_remains_1_0": True,
        "extension_version_0_2_0": True,
        "no_commit": True,
        "no_deploy": True,
        "no_publish": True,
        "no_section_reorder": True,
        "no_tag": True,
        "slice_14_9_complete": True,
        "start_epic_15": False,
    }


def build_report(monorepo: Path) -> ReportNavigationIaReport:
    contract = default_contract()
    assert contract.start_epic_15 is False
    assert contract.no_schema_change is True
    assert contract.no_section_reorder is True

    checks, defects, _meta = check_all(monorepo)
    limitations = sorted(ALLOWED_LIMITATIONS)
    failed = sum(1 for check in checks if not check.ok)
    posture = release_posture()
    if failed or defects:
        posture = {**posture, "slice_14_9_complete": False}

    return ReportNavigationIaReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=REPORT_IA_ID,
        verdict=_decide(failed, defects, limitations),
        ia_policy_status=_status(checks, "ia_policy"),
        hierarchy_status=_status(checks, "hierarchy"),
        heading_structure_status=_status(checks, "heading_structure"),
        section_header_status=_status(checks, "section_header"),
        anchor_status=_status(checks, "anchors"),
        deep_link_status=_status(checks, "deep_link"),
        toc_status=_status(checks, "toc"),
        assessment_mapping_status=_status(checks, "assessment_mapping"),
        eir_mapping_status=_status(checks, "eir_mapping"),
        executive_summary_status=_status(checks, "executive_summary"),
        metadata_status=_status(checks, "metadata"),
        findings_evidence_status=_status(checks, "findings_evidence"),
        recommendation_status=_status(checks, "recommendation"),
        supporting_detail_status=_status(checks, "supporting_detail"),
        empty_section_status=_status(checks, "empty_section"),
        section_order_status=_status(checks, "section_order"),
        responsive_navigation_status=_status(checks, "responsive_navigation"),
        print_navigation_status=_status(checks, "print_navigation"),
        commercial_boundary_status=_status(checks, "commercial_boundary"),
        visualization_boundary_status=_status(checks, "visualization_boundary"),
        asset_boundary_status=_status(checks, "asset_boundary"),
        accessibility_boundary_status=_status(checks, "accessibility_boundary"),
        deployment_boundary_status=_status(checks, "deployment_boundary"),
        schema_boundary_status=_status(checks, "schema_boundary"),
        determinism_status=_status(checks, "determinism"),
        defects=defects,
        blockers=[],
        limitations=limitations,
        checks=checks,
        total_checks=len(checks),
        failed_checks=failed,
        release_posture=posture,
    )


def write_report(monorepo: Path, report: ReportNavigationIaReport) -> Path:
    out_dir = monorepo / SV149_OUTPUT_RELATIVE
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / REPORT_JSON
    text = json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n"
    assert "timestamp" not in text
    assert "/Users/" not in text
    json_path.write_text(text, encoding="utf-8")
    (out_dir / REPORT_MD).write_text(
        f"# {SCHEMA_NAME}:{SCHEMA_VERSION}\n\n"
        f"Verdict: **{report.verdict}**\n\n"
        f"Checks: {report.total_checks} (failed: {report.failed_checks})\n\n"
        "Slice 14.9 standardizes report information architecture and navigation. "
        "Assessment and EIR remain distinct products; section order, schemas, and "
        "visualization semantics are unchanged. Slice 14.10 not started. "
        "No commit/tag/publish/deploy.\n",
        encoding="utf-8",
    )
    return json_path


def main() -> int:
    monorepo = monorepo_root_from_here()
    report = build_report(monorepo)
    path = write_report(monorepo, report)
    print(
        json.dumps(
            {
                "verdict": report.verdict,
                "report": path.name,
                "failed": report.failed_checks,
            },
            sort_keys=True,
        )
    )
    return 0 if report.verdict != "FAIL" else 1
