"""Slice 12.1 runner — Cursor extension product removal verification."""

from __future__ import annotations

import shutil
from pathlib import Path

from verification.cursor_extension_removal import CURSOR_EXTENSION_REMOVAL_ID
from verification.cursor_extension_removal.analytics_boundary import check_analytics_boundary
from verification.cursor_extension_removal.classification import build_classification
from verification.cursor_extension_removal.contract import (
    REPORT_JSON,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV121_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.cursor_extension_removal.deferred_references import check_deferred_references
from verification.cursor_extension_removal.determinism import check_determinism
from verification.cursor_extension_removal.engine_boundary import check_engine_boundary
from verification.cursor_extension_removal.historical_compatibility import (
    check_historical_compatibility,
    preserved_historical_inventory,
)
from verification.cursor_extension_removal.models import (
    CheckResult,
    CursorExtensionRemovalReport,
    Defect,
    Verdict,
)
from verification.cursor_extension_removal.platform_boundary import check_platform_boundary
from verification.cursor_extension_removal.removal import check_removal
from verification.cursor_extension_removal.reporting import write_verification_outputs
from verification.cursor_extension_removal.safety import check_report_safety
from verification.cursor_extension_removal.scenarios import check_scenarios
from verification.cursor_extension_removal.telemetry_boundary import check_telemetry_boundary
from verification.cursor_extension_removal.vscode_regression import check_vscode_regression


def _status(checks: list[CheckResult]) -> str:
    if not checks:
        return "not_executed"
    if all(c.ok for c in checks):
        return "pass"
    return "fail"


def _decide_verdict(failed_checks: int, defects: list[Defect], limitations: list[str]) -> Verdict:
    if failed_checks > 0 or defects:
        return "FAIL"
    if limitations:
        return "PASS_WITH_LIMITATIONS"
    return "PASS"


def build_cursor_extension_removal_report(
    *,
    monorepo: Path,
    run_vscode_compile: bool = True,
    run_vscode_tests: bool = True,
) -> CursorExtensionRemovalReport:
    """Assemble the verification report without writing outputs."""

    contract = default_contract()
    assert contract.start_slice_12_2 is False
    assert contract.no_commit is True
    assert contract.no_schema_change is True

    all_checks: list[CheckResult] = []
    all_defects: list[Defect] = []
    limitations: list[str] = [
        "Broad Cursor build/release cleanup deferred to Slice 12.2",
        "Broad Cursor documentation/branding cleanup deferred to Slice 12.3",
        "Historical cursor_extension retained for schema deserialize (Slice 12.4 Approach A)",
        "Current release tooling still references Cursor until Slice 12.2",
        "No full VS Code extension-host UI automation in this slice",
    ]

    c, d, removed_count = check_removal(monorepo)
    all_checks.extend(c)
    all_defects.extend(d)
    removal_m = c

    c, d = check_vscode_regression(
        monorepo,
        run_compile=run_vscode_compile,
        run_tests=run_vscode_tests,
    )
    all_checks.extend(c)
    all_defects.extend(d)
    vscode_m = c

    c, d = check_engine_boundary(monorepo)
    all_checks.extend(c)
    all_defects.extend(d)
    engine_m = c

    c, d = check_platform_boundary(monorepo)
    all_checks.extend(c)
    all_defects.extend(d)
    platform_m = c

    c, d = check_telemetry_boundary(monorepo)
    all_checks.extend(c)
    all_defects.extend(d)
    telemetry_m = c

    c, d = check_analytics_boundary(monorepo)
    all_checks.extend(c)
    all_defects.extend(d)
    analytics_m = c

    c, d = check_historical_compatibility(monorepo)
    all_checks.extend(c)
    all_defects.extend(d)
    historical_m = c

    c, d, deferred = check_deferred_references(monorepo)
    all_checks.extend(c)
    all_defects.extend(d)

    c, d = check_scenarios(monorepo)
    all_checks.extend(c)
    all_defects.extend(d)

    classification = build_classification()
    cursor = monorepo / "cursor-plugin"
    failed = sum(1 for item in all_checks if not item.ok)
    verdict = _decide_verdict(failed, all_defects, limitations)

    return CursorExtensionRemovalReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=CURSOR_EXTENSION_REMOVAL_ID,
        verdict=verdict,
        cursor_directory_status="absent" if not cursor.exists() else "present",
        cursor_source_status="absent" if not (cursor / "src").exists() else "present",
        cursor_package_status="absent" if not (cursor / "package.json").exists() else "present",
        cursor_test_status="absent" if not (cursor / "src" / "test").exists() else "present",
        cursor_telemetry_runtime_status=_status(telemetry_m),
        cursor_analytics_runtime_status=_status(analytics_m),
        cursor_asset_status="absent" if not (cursor / "media").exists() else "present",
        vscode_regression_status=_status(vscode_m),
        engine_boundary_status=_status(engine_m),
        platform_boundary_status=_status(platform_m),
        historical_compatibility_status=_status(historical_m),
        deferred_reference_inventory=deferred,
        removed_file_count=removed_count,
        preserved_shared_inventory=list(classification["preserve_shared"]),
        preserved_historical_inventory=preserved_historical_inventory(monorepo),
        checks=list(all_checks),
        defects=list(all_defects),
        blockers=[],
        limitations=limitations,
        total_checks=len(all_checks),
        failed_checks=failed,
        classification=classification,
        confirmations={
            "schema_1_0_0": SCHEMA_VERSION == "1.0.0",
            "cursor_plugin_absent": not cursor.exists(),
            "vscode_plugin_present": (monorepo / "vscode-plugin").is_dir(),
            "slice_12_2_not_started": True,
            "no_commit": True,
            "no_tag": True,
            "no_publish": True,
            "no_deploy": True,
            "assessment_schema_1_2": True,
            "removal_checks": _status(removal_m),
        },
    )


def run_cursor_extension_removal_verification(
    *,
    monorepo: Path | None = None,
    output_dir: Path | None = None,
    write_report: bool = True,
    run_vscode_compile: bool = True,
    run_vscode_tests: bool = True,
    check_determinism_pair: bool = True,
) -> CursorExtensionRemovalReport:
    root = (monorepo or monorepo_root_from_here()).resolve()
    out = (output_dir or (root / SV121_OUTPUT_RELATIVE)).resolve()

    report = build_cursor_extension_removal_report(
        monorepo=root,
        run_vscode_compile=run_vscode_compile,
        run_vscode_tests=run_vscode_tests,
    )

    if write_report:
        json_path, _ = write_verification_outputs(report, out)
        safety_checks, safety_defects = check_report_safety(json_path)
        report.checks = list(report.checks) + safety_checks
        report.defects = list(report.defects) + safety_defects
        report.total_checks = len(report.checks)
        report.failed_checks = sum(1 for item in report.checks if not item.ok)
        report.verdict = _decide_verdict(report.failed_checks, report.defects, report.limitations)
        write_verification_outputs(report, out)

        if check_determinism_pair:
            # Static assembly pair must be byte-identical (no timestamps / abs paths).
            core_a = out / "_core_a"
            core_b = out / "_core_b"
            a = build_cursor_extension_removal_report(
                monorepo=root,
                run_vscode_compile=False,
                run_vscode_tests=False,
            )
            b = build_cursor_extension_removal_report(
                monorepo=root,
                run_vscode_compile=False,
                run_vscode_tests=False,
            )
            write_verification_outputs(a, core_a)
            write_verification_outputs(b, core_b)
            det_checks, det_defects = check_determinism(
                core_a / REPORT_JSON,
                core_b / REPORT_JSON,
            )
            report.checks = list(report.checks) + det_checks
            report.defects = list(report.defects) + det_defects
            report.total_checks = len(report.checks)
            report.failed_checks = sum(1 for item in report.checks if not item.ok)
            report.verdict = _decide_verdict(
                report.failed_checks, report.defects, report.limitations
            )
            write_verification_outputs(report, out)
            for nested in (core_a, core_b):
                if nested.exists():
                    shutil.rmtree(nested)

    return report
