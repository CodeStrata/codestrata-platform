"""Slice 14.6 runner."""

from __future__ import annotations

import json
from pathlib import Path

from verification.marketplace_visual_assets import MARKETPLACE_VISUAL_ID
from verification.marketplace_visual_assets.checks import check_all
from verification.marketplace_visual_assets.contract import (
    ALLOWED_LIMITATIONS,
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV146_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.marketplace_visual_assets.models import (
    CheckResult,
    Defect,
    MarketplaceVisualAssetsReport,
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
        "extension_version_0_2_0": True,
        "no_commit": True,
        "no_deploy": True,
        "no_publish": True,
        "no_tag": True,
        "runtime_behavior_unchanged": True,
        "slice_14_6_complete": True,
        "start_slice_14_7": False,
        "universal_logo_deferred_14_10": True,
    }


def build_report(monorepo: Path) -> MarketplaceVisualAssetsReport:
    contract = default_contract()
    assert contract.start_slice_14_7 is False
    assert contract.no_universal_logo_authority_change is True

    checks, defects, meta = check_all(monorepo)
    limitations = sorted(ALLOWED_LIMITATIONS)
    failed = sum(1 for c in checks if not c.ok)
    posture = release_posture()
    if failed or defects:
        posture = {**posture, "slice_14_6_complete": False}

    return MarketplaceVisualAssetsReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=MARKETPLACE_VISUAL_ID,
        verdict=_decide(failed, defects, limitations),
        visual_policy_status=_status(checks, "visual_policy"),
        design_system_status=_status(checks, "design_system"),
        icon_status=_status(checks, "icon"),
        gallery_banner_status=_status(checks, "gallery_banner"),
        screenshot_manifest_status=_status(checks, "screenshot_manifest"),
        screenshot_dimension_status=_status(checks, "screenshot_dimensions"),
        screenshot_safety_status=_status(checks, "screenshot_safety"),
        screenshot_metadata_status=_status(checks, "screenshot_metadata"),
        screenshot_content_status=_status(checks, "screenshot_content"),
        gallery_order_status=_status(checks, "gallery_order"),
        caption_status=_status(checks, "captions"),
        alt_text_status=_status(checks, "alt_text"),
        legacy_asset_status=_status(checks, "legacy_assets"),
        cursor_absence_status=_status(checks, "cursor_absence"),
        commercial_boundary_status=_status(checks, "commercial_boundary"),
        package_inventory_status=_status(checks, "package_inventory"),
        asset_size_status=_status(checks, "asset_size"),
        readme_reference_status=_status(checks, "readme_reference"),
        vscode_visual_boundary_status=_status(checks, "vscode_visual_boundary"),
        logo_boundary_status=_status(checks, "logo_boundary"),
        accessibility_status=_status(checks, "accessibility"),
        vscode_regression_status=_status(checks, "vscode_regression"),
        determinism_status=_status(checks, "determinism"),
        defects=defects,
        blockers=[],
        limitations=limitations,
        checks=checks,
        total_checks=len(checks),
        failed_checks=failed,
        release_posture=posture,
        asset_size_summary={
            "media_count": meta.get("media_count", 0),
            "media_bytes": meta.get("media_bytes", 0),
            "vs_historical_media_category": "major_reduction",
        },
    )


def write_report(monorepo: Path, report: MarketplaceVisualAssetsReport) -> Path:
    out_dir = monorepo / SV146_OUTPUT_RELATIVE
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
        "Slice 14.6 aligns Marketplace visual assets to Design System 1.0. "
        "Marketplace copy semantics unchanged. Universal logo deferred to 14.10. "
        "Slice 14.7 not started. No commit/tag/publish/deploy.\n",
        encoding="utf-8",
    )
    return json_path


def main() -> int:
    monorepo = monorepo_root_from_here()
    report = build_report(monorepo)
    path = write_report(monorepo, report)
    print(json.dumps({"verdict": report.verdict, "report": str(path.name)}, sort_keys=True))
    return 0 if report.verdict != "FAIL" else 1
