"""Slice 14.1 runner."""

from __future__ import annotations

import json
from pathlib import Path

from verification.visual_design_system import VISUAL_DESIGN_SYSTEM_ID
from verification.visual_design_system.checks import check_all, release_posture
from verification.visual_design_system.contract import (
    ALLOWED_LIMITATIONS,
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV141_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.visual_design_system.models import (
    CheckResult,
    Defect,
    Verdict,
    VisualDesignSystemReport,
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


def build_report(monorepo: Path) -> VisualDesignSystemReport:
    contract = default_contract()
    assert contract.start_slice_14_2 is False
    assert contract.product_redesign_allowed is False

    checks, defects = check_all(monorepo)
    limitations = sorted(ALLOWED_LIMITATIONS)
    failed = sum(1 for c in checks if not c.ok)
    posture = release_posture()
    if failed or defects:
        posture = {**posture, "slice_14_1_complete": False}

    return VisualDesignSystemReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=VISUAL_DESIGN_SYSTEM_ID,
        verdict=_decide(failed, defects, limitations),
        tokens_status=_status(checks, "tokens"),
        colors_status=_status(checks, "colors"),
        typography_status=_status(checks, "typography"),
        spacing_status=_status(checks, "spacing"),
        components_status=_status(checks, "components"),
        report_language_status=_status(checks, "report_language"),
        documentation_language_status=_status(checks, "documentation_language"),
        vscode_language_status=_status(checks, "vscode_language"),
        marketplace_language_status=_status(checks, "marketplace_language"),
        accessibility_status=_status(checks, "accessibility"),
        responsive_status=_status(checks, "responsive"),
        no_redesign_status=_status(checks, "no_redesign"),
        slice_14_2_absence_status=_status(checks, "slice_14_2"),
        release_posture=posture,
        defects=defects,
        blockers=[],
        limitations=limitations,
        checks=checks,
        total_checks=len(checks),
        failed_checks=failed,
    )


def write_report(monorepo: Path, report: VisualDesignSystemReport) -> Path:
    out_dir = monorepo / SV141_OUTPUT_RELATIVE
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
        "Slice 14.1 defines the CodeStrata Visual Design System only. "
        "No product redesign. Slice 14.2 not started. "
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
