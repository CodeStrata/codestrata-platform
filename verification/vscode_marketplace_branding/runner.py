"""Slice 13.12 runner."""

from __future__ import annotations

import json
from pathlib import Path

from verification.vscode_marketplace_branding import VSCODE_MARKETPLACE_BRANDING_ID
from verification.vscode_marketplace_branding.checks import check_all
from verification.vscode_marketplace_branding.contract import (
    ALLOWED_LIMITATIONS,
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV1312_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.vscode_marketplace_branding.models import (
    CheckResult,
    Defect,
    Verdict,
    VsCodeMarketplaceBrandingReport,
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


def build_report(monorepo: Path) -> VsCodeMarketplaceBrandingReport:
    contract = default_contract()
    assert contract.start_epic_14 is False
    assert contract.no_publish is True

    checks, defects = check_all(monorepo)
    limitations = sorted(ALLOWED_LIMITATIONS)
    failed = sum(1 for c in checks if not c.ok)
    return VsCodeMarketplaceBrandingReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=VSCODE_MARKETPLACE_BRANDING_ID,
        verdict=_decide(failed, defects, limitations),
        branding_policy_status=_status(checks, "branding_policy"),
        product_naming_status=_status(checks, "product_naming"),
        metadata_status=_status(checks, "metadata"),
        icon_status=_status(checks, "icon"),
        gallery_banner_status=_status(checks, "gallery_banner"),
        screenshot_status=_status(checks, "screenshot"),
        gallery_order_status=_status(checks, "gallery_order"),
        asset_safety_status=_status(checks, "asset_safety"),
        package_inventory_status=_status(checks, "package_inventory"),
        cursor_absence_status=_status(checks, "cursor_absence"),
        claim_review_status=_status(checks, "claim_review"),
        accessibility_status=_status(checks, "accessibility"),
        link_inventory_status=_status(checks, "link_inventory"),
        website_reference_status=_status(checks, "website_reference"),
        vscode_regression_status=_status(checks, "vscode_regression"),
        deferred_marketplace_documentation_status=_status(
            checks, "deferred_marketplace_documentation"
        ),
        defects=defects,
        blockers=[],
        limitations=limitations,
        checks=checks,
        total_checks=len(checks),
        failed_checks=failed,
    )


def write_report(monorepo: Path, report: VsCodeMarketplaceBrandingReport) -> Path:
    out_dir = monorepo / SV1312_OUTPUT_RELATIVE
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / REPORT_JSON
    payload = report.to_dict()
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    # Privacy guard on written report
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
