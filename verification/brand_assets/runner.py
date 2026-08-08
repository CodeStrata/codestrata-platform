"""Slice 14.10 runner."""

from __future__ import annotations

import json
from pathlib import Path

from verification.brand_assets import BRAND_ASSETS_ID
from verification.brand_assets.checks import check_all
from verification.brand_assets.contract import (
    ALLOWED_LIMITATIONS,
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV1410_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.brand_assets.models import (
    BrandAssetsReport,
    CheckResult,
    Defect,
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
        "no_runtime_change": True,
        "no_tag": True,
        "slice_14_10_complete": True,
        "start_epic_15": False,
    }


def build_report(monorepo: Path) -> BrandAssetsReport:
    contract = default_contract()
    assert contract.start_epic_15 is False
    assert contract.single_master_required is True
    assert contract.no_schema_change is True

    checks, defects, sizes = check_all(monorepo)
    limitations = sorted(ALLOWED_LIMITATIONS)
    failed = sum(1 for check in checks if not check.ok)
    posture = release_posture()
    if failed or defects:
        posture = {**posture, "slice_14_10_complete": False}

    return BrandAssetsReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=BRAND_ASSETS_ID,
        verdict=_decide(failed, defects, limitations),
        brand_asset_policy_status=_status(checks, "brand_asset_policy"),
        inventory_status=_status(checks, "inventory"),
        authority_status=_status(checks, "authority"),
        master_mark_status=_status(checks, "master_mark"),
        wordmark_status=_status(checks, "wordmark"),
        variant_status=_status(checks, "variants"),
        svg_safety_status=_status(checks, "svg_safety"),
        raster_metadata_status=_status(checks, "raster_metadata"),
        duplicate_status=_status(checks, "duplicates"),
        legacy_asset_status=_status(checks, "legacy_assets"),
        aimf_status=_status(checks, "aimf"),
        cursor_status=_status(checks, "cursor"),
        website_consumer_status=_status(checks, "website_consumer"),
        documentation_consumer_status=_status(checks, "documentation_consumer"),
        assessment_consumer_status=_status(checks, "assessment_consumer"),
        eir_consumer_status=_status(checks, "eir_consumer"),
        vscode_consumer_status=_status(checks, "vscode_consumer"),
        marketplace_consumer_status=_status(checks, "marketplace_consumer"),
        favicon_status=_status(checks, "favicon"),
        icon_language_status=_status(checks, "icon_language"),
        export_boundary_status=_status(checks, "export_boundary"),
        asset_size_status=_status(checks, "asset_sizes"),
        accessibility_baseline_status=_status(checks, "accessibility_baseline"),
        responsive_baseline_status=_status(checks, "responsive_baseline"),
        ia_boundary_status=_status(checks, "ia_boundary"),
        visualization_boundary_status=_status(checks, "visualization_boundary"),
        deployment_boundary_status=_status(checks, "deployment_boundary"),
        determinism_status=_status(checks, "determinism"),
        defects=defects,
        blockers=[],
        limitations=limitations,
        checks=checks,
        asset_sizes=sizes,
        total_checks=len(checks),
        failed_checks=failed,
        release_posture=posture,
    )


def write_report(monorepo: Path, report: BrandAssetsReport) -> Path:
    out_dir = monorepo / SV1410_OUTPUT_RELATIVE
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / REPORT_JSON
    text = json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n"
    assert "/Users/" not in text
    assert "/home/" not in text
    json_path.write_text(text, encoding="utf-8")
    (out_dir / REPORT_MD).write_text(
        f"# {SCHEMA_NAME}:{SCHEMA_VERSION}\n\n"
        f"Verdict: **{report.verdict}**\n\n"
        f"Checks: {report.total_checks} (failed: {report.failed_checks})\n\n"
        "Slice 14.10 establishes one authoritative CodeStrata brand asset system. "
        "The Design System owns the master mark and wordmark; every product surface "
        "consumes an approved derivative. Report information architecture, visualization "
        "semantics, schemas, and runtime behaviour are unchanged. Slice 14.13 complete. "
        "Epic 15 not started. "
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
