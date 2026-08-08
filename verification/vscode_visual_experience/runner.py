"""Slice 14.5 runner."""

from __future__ import annotations

import json
from pathlib import Path

from verification.vscode_visual_experience import VSCODE_VISUAL_ID
from verification.vscode_visual_experience.contract import (
    ALLOWED_LIMITATIONS,
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV145_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.vscode_visual_experience.models import (
    CheckResult,
    Defect,
    Verdict,
    VsCodeVisualReport,
)
from verification.vscode_visual_experience.reporting import release_posture, run_checks


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


def build_report(monorepo: Path) -> VsCodeVisualReport:
    assert default_contract().start_slice_14_6 is False
    checks, defects, meta = run_checks(monorepo)
    limitations = sorted(ALLOWED_LIMITATIONS)
    failed = sum(1 for c in checks if not c.ok)
    posture = release_posture()
    if failed or defects:
        posture = {**posture, "slice_14_5_complete": False}

    return VsCodeVisualReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=VSCODE_VISUAL_ID,
        verdict=_decide(failed, defects, limitations),
        visual_policy_status=_status(checks, "visual_policy"),
        design_system_mapping_status=_status(checks, "design_system_mapping"),
        native_host_boundary_status=_status(checks, "native_host_boundary"),
        product_naming_status=_status(checks, "product_naming"),
        command_title_status=_status(checks, "command_title"),
        activity_bar_status=_status(checks, "activity_bar"),
        first_run_status=_status(checks, "first_run"),
        messaging_status=_status(checks, "messaging"),
        progress_status=_status(checks, "progress"),
        status_bar_status=_status(checks, "status_bar"),
        recovery_status=_status(checks, "recovery"),
        report_ready_status=_status(checks, "report_ready"),
        cli_guidance_status=_status(checks, "cli_guidance"),
        doctor_status=_status(checks, "doctor"),
        settings_status=_status(checks, "settings"),
        output_channel_status=_status(checks, "output_channel"),
        icon_status=_status(checks, "icon"),
        welcome_state_status=_status(checks, "welcome_state"),
        community_scope_status=_status(checks, "community_scope"),
        privacy_wording_status=_status(checks, "privacy_wording"),
        telemetry_wording_status=_status(checks, "telemetry_wording"),
        theme_compatibility_status=_status(checks, "theme_compatibility"),
        accessibility_status=_status(checks, "accessibility"),
        marketplace_boundary_status=_status(checks, "marketplace_boundary"),
        asset_boundary_status=_status(checks, "asset_boundary"),
        legacy_branding_status=_status(checks, "legacy_branding"),
        vscode_regression_status=_status(checks, "vscode_regression"),
        determinism_status=_status(checks, "determinism"),
        release_posture=posture,
        defects=defects,
        blockers=[],
        limitations=limitations,
        checks=checks,
        total_checks=len(checks),
        failed_checks=failed,
    )


def write_report(monorepo: Path, report: VsCodeVisualReport) -> Path:
    out_dir = monorepo / SV145_OUTPUT_RELATIVE
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / REPORT_JSON
    text = json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n"
    assert "/Users/" not in text
    assert "file://" not in text
    assert '"timestamp"' not in text
    json_path.write_text(text, encoding="utf-8")
    (out_dir / REPORT_MD).write_text(
        f"# {SCHEMA_NAME}:{SCHEMA_VERSION}\n\n"
        f"Verdict: **{report.verdict}**\n\n"
        f"Checks: {report.total_checks} (failed: {report.failed_checks})\n\n"
        "Slice 14.5 aligns VS Code presentation with Design System 1.0 using "
        "native host surfaces. Runtime behavior and Marketplace assets unchanged. "
        "Slice 14.6 not started. No commit/tag/publish/deploy.\n",
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
