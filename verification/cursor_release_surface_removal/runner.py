"""Slice 12.2 runner — Cursor release-surface removal verification."""

from __future__ import annotations

import shutil
from pathlib import Path

from verification.cursor_release_surface_removal import CURSOR_RELEASE_SURFACE_REMOVAL_ID
from verification.cursor_release_surface_removal.contract import (
    REPORT_JSON,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV122_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.cursor_release_surface_removal.determinism import check_determinism
from verification.cursor_release_surface_removal.engine_boundary import (
    check_engine_boundary,
    check_platform_boundary,
)
from verification.cursor_release_surface_removal.historical_references import (
    check_deferred_documentation,
    check_historical_references,
)
from verification.cursor_release_surface_removal.models import (
    CheckResult,
    CursorReleaseSurfaceRemovalReport,
    Defect,
    Verdict,
)
from verification.cursor_release_surface_removal.reporting import write_verification_outputs
from verification.cursor_release_surface_removal.safety import check_report_safety
from verification.cursor_release_surface_removal.scenarios import check_scenarios
from verification.cursor_release_surface_removal.surfaces import (
    check_build_surfaces,
    check_checksums_and_licensing,
    check_ci_boundary,
    check_marketplace_surfaces,
    check_package_surfaces,
    check_publishing,
    check_release_artifacts,
    check_release_inventory,
    check_versions_surface,
    removed_reference_count,
)
from verification.cursor_release_surface_removal.vscode_regression import check_vscode_regression


def _status(checks: list[CheckResult]) -> str:
    if not checks:
        return "not_executed"
    return "pass" if all(c.ok for c in checks) else "fail"


def _decide_verdict(failed_checks: int, defects: list[Defect], limitations: list[str]) -> Verdict:
    if failed_checks > 0 or defects:
        return "FAIL"
    if limitations:
        return "PASS_WITH_LIMITATIONS"
    return "PASS"


def build_cursor_release_surface_removal_report(
    *,
    monorepo: Path,
    run_vscode_compile: bool = True,
    run_vscode_tests: bool = True,
    run_vscode_package: bool = True,
) -> CursorReleaseSurfaceRemovalReport:
    contract = default_contract()
    assert contract.start_slice_12_3 is False
    assert contract.no_commit is True

    all_checks: list[CheckResult] = []
    all_defects: list[Defect] = []
    limitations = [
        "Broad Cursor documentation/branding cleanup deferred to Slice 12.3",
        "Historical cursor_extension retained for schema deserialize (Slice 12.4 Approach A)",
        "Infrastructure export redesign deferred",
        "No live Marketplace upload in this slice",
        "No final release artifact publication in this slice",
        "No full VS Code extension-host UI automation",
    ]

    buckets: dict[str, list[CheckResult]] = {}

    def take(name: str, pair: tuple[list[CheckResult], list[Defect]]) -> None:
        c, d = pair
        buckets[name] = c
        all_checks.extend(c)
        all_defects.extend(d)

    take("build", check_build_surfaces(monorepo))
    take("package", check_package_surfaces(monorepo))
    take("marketplace", check_marketplace_surfaces(monorepo))
    take("release_inventory", check_release_inventory(monorepo))
    take("release_artifacts", check_release_artifacts(monorepo))
    take("versions", check_versions_surface(monorepo))
    take("checksum_license", check_checksums_and_licensing(monorepo))
    take("publishing", check_publishing(monorepo))
    take("ci", check_ci_boundary(monorepo))

    c, d = check_vscode_regression(
        monorepo,
        run_compile=run_vscode_compile,
        run_tests=run_vscode_tests,
        run_package=run_vscode_package,
    )
    buckets["vscode"] = c
    all_checks.extend(c)
    all_defects.extend(d)

    take("engine", check_engine_boundary(monorepo))
    take("platform", check_platform_boundary(monorepo))
    take("historical", check_historical_references(monorepo))

    c, d, deferred = check_deferred_documentation(monorepo)
    buckets["deferred"] = c
    all_checks.extend(c)
    all_defects.extend(d)

    take("scenarios", check_scenarios(monorepo))

    failed = sum(1 for item in all_checks if not item.ok)
    verdict = _decide_verdict(failed, all_defects, limitations)

    # Split checksum/license statuses from combined bucket
    checksum_checks = [x for x in buckets["checksum_license"] if x.category == "checksums"]
    license_checks = [x for x in buckets["checksum_license"] if x.category == "licensing"]
    vscode_build = [x for x in buckets["vscode"] if "compile" in x.name or "npm_test" in x.name]
    vscode_pkg = [x for x in buckets["vscode"] if "package" in x.name or "vsce" in x.name]
    vscode_rel = [x for x in buckets["vscode"] if "version" in x.name or "package_name" in x.name]

    return CursorReleaseSurfaceRemovalReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=CURSOR_RELEASE_SURFACE_REMOVAL_ID,
        verdict=verdict,
        cursor_build_surface_status=_status(buckets["build"]),
        cursor_package_surface_status=_status(buckets["package"]),
        cursor_marketplace_surface_status=_status(buckets["marketplace"]),
        cursor_release_inventory_status=_status(buckets["release_inventory"]),
        cursor_release_artifact_status=_status(buckets["release_artifacts"]),
        cursor_version_status=_status(buckets["versions"]),
        cursor_checksum_status=_status(checksum_checks),
        cursor_license_status=_status(license_checks),
        cursor_publish_status=_status(buckets["publishing"]),
        cursor_ci_status=_status(buckets["ci"]),
        vscode_build_status=_status(vscode_build) if vscode_build else _status(buckets["vscode"]),
        vscode_package_status=_status(vscode_pkg) if vscode_pkg else _status(buckets["vscode"]),
        vscode_release_status=_status(vscode_rel) if vscode_rel else _status(buckets["vscode"]),
        engine_release_boundary_status=_status(buckets["engine"]),
        platform_release_boundary_status=_status(buckets["platform"]),
        historical_reference_status=_status(buckets["historical"]),
        deferred_documentation_inventory=deferred,
        removed_reference_count=removed_reference_count(),
        checks=list(all_checks),
        defects=list(all_defects),
        blockers=[],
        limitations=limitations,
        total_checks=len(all_checks),
        failed_checks=failed,
        confirmations={
            "schema_1_0_0": SCHEMA_VERSION == "1.0.0",
            "slice_12_3_not_started": True,
            "no_commit": True,
            "no_tag": True,
            "no_publish": True,
            "no_deploy": True,
            "vscode_only_editor_extension": True,
            "assessment_schema_1_2": True,
        },
    )


def run_cursor_release_surface_removal_verification(
    *,
    monorepo: Path | None = None,
    output_dir: Path | None = None,
    write_report: bool = True,
    run_vscode_compile: bool = True,
    run_vscode_tests: bool = True,
    run_vscode_package: bool = True,
    check_determinism_pair: bool = True,
) -> CursorReleaseSurfaceRemovalReport:
    root = (monorepo or monorepo_root_from_here()).resolve()
    out = (output_dir or (root / SV122_OUTPUT_RELATIVE)).resolve()

    report = build_cursor_release_surface_removal_report(
        monorepo=root,
        run_vscode_compile=run_vscode_compile,
        run_vscode_tests=run_vscode_tests,
        run_vscode_package=run_vscode_package,
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
            core_a = out / "_core_a"
            core_b = out / "_core_b"
            a = build_cursor_release_surface_removal_report(
                monorepo=root,
                run_vscode_compile=False,
                run_vscode_tests=False,
                run_vscode_package=False,
            )
            b = build_cursor_release_surface_removal_report(
                monorepo=root,
                run_vscode_compile=False,
                run_vscode_tests=False,
                run_vscode_package=False,
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
