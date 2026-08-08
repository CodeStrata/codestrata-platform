"""Slice 14.7 runner."""

from __future__ import annotations

import json
from pathlib import Path

from verification.cross_surface_presentation import CROSS_SURFACE_ID
from verification.cross_surface_presentation.checks import check_all
from verification.cross_surface_presentation.contract import (
    ALLOWED_LIMITATIONS,
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV147_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.cross_surface_presentation.models import (
    CheckResult,
    Defect,
    CrossSurfacePresentationReport,
    Verdict,
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
        "design_system_remains_1_0": True,
        "extension_version_0_2_0": True,
        "no_commit": True,
        "no_deploy": True,
        "no_publish": True,
        "no_tag": True,
        "runtime_behavior_unchanged": True,
        "slice_14_7_complete": True,
        "start_epic_15": False,
    }


def build_report(monorepo: Path) -> CrossSurfacePresentationReport:
    contract = default_contract()
    assert contract.start_epic_15 is False

    checks, defects, _meta = check_all(monorepo)
    limitations = sorted(ALLOWED_LIMITATIONS)
    failed = sum(1 for c in checks if not c.ok)
    posture = release_posture()
    if failed or defects:
        posture = {**posture, "slice_14_7_complete": False}

    return CrossSurfacePresentationReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=CROSS_SURFACE_ID,
        verdict=_decide(failed, defects, limitations),
        visual_policy_status=_status(checks, "visual_policy"),
        token_authority_status=_status(checks, "token_authority"),
        typography_status=_status(checks, "typography"),
        typography_delivery_status=_status(checks, "typography_delivery"),
        colors_status=_status(checks, "colors"),
        surfaces_status=_status(checks, "surfaces"),
        spacing_status=_status(checks, "spacing"),
        radii_status=_status(checks, "radii"),
        borders_status=_status(checks, "borders"),
        shadows_status=_status(checks, "shadows"),
        layouts_status=_status(checks, "layouts"),
        components_status=_status(checks, "components"),
        cards_status=_status(checks, "cards"),
        tables_status=_status(checks, "tables"),
        code_evidence_status=_status(checks, "code_evidence"),
        callouts_status=_status(checks, "callouts"),
        actions_status=_status(checks, "actions"),
        docs_consumer_status=_status(checks, "docs_consumer"),
        assessment_consumer_status=_status(checks, "assessment_consumer"),
        eir_consumer_status=_status(checks, "eir_consumer"),
        vscode_consumer_status=_status(checks, "vscode_consumer"),
        marketplace_consumer_status=_status(checks, "marketplace_consumer"),
        legacy_status=_status(checks, "legacy"),
        duplication_status=_status(checks, "duplication"),
        chart_boundary_status=_status(checks, "chart_boundary"),
        navigation_boundary_status=_status(checks, "navigation_boundary"),
        asset_boundary_status=_status(checks, "asset_boundary"),
        accessibility_boundary_status=_status(checks, "accessibility_boundary"),
        determinism_status=_status(checks, "determinism"),
        defects=defects,
        blockers=[],
        limitations=limitations,
        checks=checks,
        total_checks=len(checks),
        failed_checks=failed,
        release_posture=posture,
    )


def write_report(monorepo: Path, report: CrossSurfacePresentationReport) -> Path:
    out_dir = monorepo / SV147_OUTPUT_RELATIVE
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
        "Slice 14.7 standardizes cross-surface presentation contracts. "
        "Design System remains 1.0. Charts deferred to 14.8. "
        "Slice 14.8 not started. No commit/tag/publish/deploy.\n",
        encoding="utf-8",
    )
    return json_path


def main() -> int:
    monorepo = monorepo_root_from_here()
    report = build_report(monorepo)
    path = write_report(monorepo, report)
    print(
        json.dumps(
            {"verdict": report.verdict, "report": path.name, "failed": report.failed_checks},
            sort_keys=True,
        )
    )
    return 0 if report.verdict != "FAIL" else 1
