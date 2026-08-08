"""Slice 14.8 runner."""

from __future__ import annotations

import json
from pathlib import Path

from verification.visualization_system import VISUALIZATION_ID
from verification.visualization_system.checks import check_all
from verification.visualization_system.contract import (
    ALLOWED_LIMITATIONS,
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV148_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.visualization_system.models import (
    CheckResult,
    Defect,
    Verdict,
    VisualizationSystemReport,
)


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


def release_posture() -> dict[str, bool]:
    return {
        "assessment_schema_1_2": True,
        "design_system_remains_1_0": True,
        "extension_version_0_2_0": True,
        "no_commit": True,
        "no_deploy": True,
        "no_publish": True,
        "no_scoring_change": True,
        "no_tag": True,
        "slice_14_8_complete": True,
        "start_epic_15": False,
    }


def build_report(monorepo: Path) -> VisualizationSystemReport:
    contract = default_contract()
    assert contract.start_epic_15 is False
    assert contract.no_scoring_change is True

    checks, defects, _meta = check_all(monorepo)
    limitations = sorted(ALLOWED_LIMITATIONS)
    failed = sum(1 for c in checks if not c.ok)
    posture = release_posture()
    if failed or defects:
        posture = {**posture, "slice_14_8_complete": False}

    return VisualizationSystemReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=VISUALIZATION_ID,
        verdict=_decide(failed, defects, limitations),
        visualization_policy_status=_status(checks, "visualization_policy"),
        domain_semantics_status=_status(checks, "domain_semantics"),
        semantic_role_status=_status(checks, "semantic_role"),
        risk_status=_status(checks, "risk"),
        severity_status=_status(checks, "severity"),
        status_visualization_status=_status(checks, "status_visualization"),
        confidence_status=_status(checks, "confidence"),
        score_status=_status(checks, "score"),
        score_component_status=_status(checks, "score_component"),
        palette_status=_status(checks, "palette"),
        chart_contract_status=_status(checks, "chart_contract"),
        chart_inventory_status=_status(checks, "chart_inventory"),
        legend_status=_status(checks, "legend"),
        empty_state_status=_status(checks, "empty_state"),
        assessment_mapping_status=_status(checks, "assessment_mapping"),
        eir_mapping_status=_status(checks, "eir_mapping"),
        docs_boundary_status=_status(checks, "docs_boundary"),
        marketplace_boundary_status=_status(checks, "marketplace_boundary"),
        vscode_boundary_status=_status(checks, "vscode_boundary"),
        dark_theme_status=_status(checks, "dark_theme"),
        print_status=_status(checks, "print"),
        accessibility_baseline_status=_status(checks, "accessibility_baseline"),
        schema_boundary_status=_status(checks, "schema_boundary"),
        navigation_boundary_status=_status(checks, "navigation_boundary"),
        asset_boundary_status=_status(checks, "asset_boundary"),
        determinism_status=_status(checks, "determinism"),
        defects=defects,
        blockers=[],
        limitations=limitations,
        checks=checks,
        total_checks=len(checks),
        failed_checks=failed,
        release_posture=posture,
    )


def write_report(monorepo: Path, report: VisualizationSystemReport) -> Path:
    out_dir = monorepo / SV148_OUTPUT_RELATIVE
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
        "Slice 14.8 standardizes visualization grammar. Domain truth unchanged. "
        "Charts foundation defined without inventing dashboards. "
        "Slice 14.9 not started. No commit/tag/publish/deploy.\n",
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
