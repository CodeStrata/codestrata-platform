"""Slice 13.13 runner."""

from __future__ import annotations

import json
from pathlib import Path

from verification.vscode_marketplace_docs import VSCODE_MARKETPLACE_DOCS_ID
from verification.vscode_marketplace_docs.checks import check_all
from verification.vscode_marketplace_docs.contract import (
    ALLOWED_LIMITATIONS,
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV1313_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.vscode_marketplace_docs.models import (
    CheckResult,
    Defect,
    Verdict,
    VsCodeMarketplaceDocsReport,
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


def build_report(monorepo: Path) -> VsCodeMarketplaceDocsReport:
    contract = default_contract()
    assert contract.start_epic_14 is False
    assert contract.no_publish is True

    checks, defects = check_all(monorepo)
    limitations = sorted(ALLOWED_LIMITATIONS)
    failed = sum(1 for c in checks if not c.ok)
    return VsCodeMarketplaceDocsReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=VSCODE_MARKETPLACE_DOCS_ID,
        verdict=_decide(failed, defects, limitations),
        documentation_policy_status=_status(checks, "documentation_policy"),
        structure_status=_status(checks, "structure"),
        claim_matrix_status=_status(checks, "claim_matrix"),
        workflow_status=_status(checks, "workflow"),
        installation_status=_status(checks, "installation"),
        initialization_status=_status(checks, "initialization"),
        assessment_status=_status(checks, "assessment"),
        ai_status=_status(checks, "ai"),
        progress_status=_status(checks, "progress"),
        report_status=_status(checks, "report"),
        recovery_status=_status(checks, "recovery"),
        compatibility_status=_status(checks, "compatibility"),
        telemetry_status=_status(checks, "telemetry"),
        locality_status=_status(checks, "locality"),
        privacy_status=_status(checks, "privacy"),
        security_status=_status(checks, "security"),
        screenshot_status=_status(checks, "screenshot"),
        link_status=_status(checks, "link"),
        cursor_absence_status=_status(checks, "cursor_absence"),
        cloud_claim_status=_status(checks, "cloud_claim"),
        internal_boundary_status=_status(checks, "internal_boundary"),
        package_rendering_status=_status(checks, "package_rendering"),
        accessibility_status=_status(checks, "accessibility"),
        vscode_regression_status=_status(checks, "vscode_regression"),
        deferred_clean_install_status=_status(checks, "deferred_clean_install"),
        defects=defects,
        blockers=[],
        limitations=limitations,
        checks=checks,
        total_checks=len(checks),
        failed_checks=failed,
    )


def write_report(monorepo: Path, report: VsCodeMarketplaceDocsReport) -> Path:
    out_dir = monorepo / SV1313_OUTPUT_RELATIVE
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
        "Epic 14 Product Experience not started. "
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
        f"checks={report.total_checks} failed={report.failed_checks}"
    )
    for check in report.checks:
        if not check.ok:
            print(f"  FAIL {check.name}: {check.detail}")
    print(f"report={path}")
    return 0 if report.verdict != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
