"""Slice 14.2 runner."""

from __future__ import annotations

import json
from pathlib import Path

from verification.community_documentation_redesign import COMMUNITY_DOCS_REDESIGN_ID
from verification.community_documentation_redesign.checks import check_all, release_posture
from verification.community_documentation_redesign.contract import (
    ALLOWED_LIMITATIONS,
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV142_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_documentation_redesign.models import (
    CheckResult,
    Defect,
    Verdict,
    CommunityDocsRedesignReport,
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


def build_report(monorepo: Path) -> CommunityDocsRedesignReport:
    contract = default_contract()
    assert contract.start_slice_14_3 is False
    assert contract.no_assessment_html_redesign is True

    checks, defects, meta = check_all(monorepo)
    limitations = sorted(ALLOWED_LIMITATIONS)
    failed = sum(1 for c in checks if not c.ok)
    posture = release_posture()
    if failed or defects:
        posture = {**posture, "slice_14_2_complete": False}

    return CommunityDocsRedesignReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=COMMUNITY_DOCS_REDESIGN_ID,
        verdict=_decide(failed, defects, limitations),
        design_system_consumed=bool(meta.get("design_system_consumed")),
        community_only_scope=bool(meta.get("community_only_scope")),
        tokens_status=_status(checks, "tokens"),
        navigation_status=_status(checks, "navigation"),
        components_status=_status(checks, "components"),
        typography_status=_status(checks, "typography"),
        accessibility_status=_status(checks, "accessibility"),
        responsive_status=_status(checks, "responsive"),
        dark_mode_status=_status(checks, "dark_mode"),
        mobile_status=_status(checks, "mobile"),
        no_product_redesign_status=_status(checks, "no_product_redesign"),
        slice_14_8_absence_status=_status(checks, "slice_14_8"),
        release_posture=posture,
        defects=defects,
        blockers=[],
        limitations=limitations,
        checks=checks,
        total_checks=len(checks),
        failed_checks=failed,
    )


def write_report(monorepo: Path, report: CommunityDocsRedesignReport) -> Path:
    out_dir = monorepo / SV142_OUTPUT_RELATIVE
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
        "Slice 14.2 rebuilds Community documentation on the Design System. "
        "No Assessment HTML / EIR / VS Code / Marketplace redesign. "
        "Slice 14.3 not started. No commit/tag/publish/deploy.\n",
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
