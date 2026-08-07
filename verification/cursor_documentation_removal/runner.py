"""Slice 12.3 runner."""

from __future__ import annotations

import shutil
from pathlib import Path

from verification.cursor_documentation_removal import CURSOR_DOCUMENTATION_REMOVAL_ID
from verification.cursor_documentation_removal.checks import (
    check_architecture,
    check_branding_assets,
    check_cli_configuration_docs,
    check_cloud_data_lake_docs,
    check_extension_docs,
    check_historical_and_deferred,
    check_marketplace_docs,
    check_privacy,
    check_removed_paths,
    check_root_readme,
    check_security,
    check_telemetry_analytics_docs,
    check_vscode_documentation,
    counts,
)
from verification.cursor_documentation_removal.contract import (
    REPORT_JSON,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV123_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.cursor_documentation_removal.models import (
    CheckResult,
    CursorDocumentationRemovalReport,
    Defect,
    Verdict,
)
from verification.cursor_documentation_removal.reporting import write_verification_outputs
from verification.cursor_documentation_removal.safety import check_determinism, check_report_safety
from verification.cursor_documentation_removal.scenarios import check_scenarios


def _status(checks: list[CheckResult]) -> str:
    if not checks:
        return "not_executed"
    return "pass" if all(c.ok for c in checks) else "fail"


def _decide(failed: int, defects: list[Defect], limitations: list[str]) -> Verdict:
    if failed or defects:
        return "FAIL"
    if limitations:
        return "PASS_WITH_LIMITATIONS"
    return "PASS"


def build_report(monorepo: Path) -> CursorDocumentationRemovalReport:
    contract = default_contract()
    assert contract.start_slice_12_4 is False
    assert contract.no_runtime_change is True

    all_checks: list[CheckResult] = []
    all_defects: list[Defect] = []
    buckets: dict[str, list[CheckResult]] = {}

    def take(name: str, pair: tuple[list[CheckResult], list[Defect]]) -> None:
        c, d = pair
        buckets[name] = c
        all_checks.extend(c)
        all_defects.extend(d)

    take("root", check_root_readme(monorepo))
    take("architecture", check_architecture(monorepo))
    take("privacy", check_privacy(monorepo))
    take("security", check_security(monorepo))
    take("extension", check_extension_docs(monorepo))
    take("marketplace", check_marketplace_docs(monorepo))
    take("branding", check_branding_assets(monorepo))
    take("cli_config", check_cli_configuration_docs(monorepo))
    take("telemetry", check_telemetry_analytics_docs(monorepo))
    take("cloud", check_cloud_data_lake_docs(monorepo))
    take("vscode", check_vscode_documentation(monorepo))
    take("removal", check_removed_paths(monorepo))

    c, d, deferred = check_historical_and_deferred(monorepo)
    buckets["historical"] = c
    all_checks.extend(c)
    all_defects.extend(d)

    take("scenarios", check_scenarios(monorepo))

    removed_docs, changed_docs, removed_assets = counts()
    limitations = [
        "cursor_extension retained for historical schema deserialize (Slice 12.4 Approach A)",
        "Clearly historical Cursor references retained where labeled former/removed",
        "Contributor Cursor IDE assistant instructions (governance/ai) retained as non-product tooling",
        "No full documentation-site rendering validation in this slice",
        "No Marketplace upload validation",
        "Infrastructure repository work deferred",
    ]
    failed = sum(1 for x in all_checks if not x.ok)
    return CursorDocumentationRemovalReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=CURSOR_DOCUMENTATION_REMOVAL_ID,
        verdict=_decide(failed, all_defects, limitations),
        root_readme_status=_status(buckets["root"]),
        architecture_status=_status(buckets["architecture"]),
        privacy_status=_status(buckets["privacy"]),
        security_status=_status(buckets["security"]),
        extension_documentation_status=_status(buckets["extension"]),
        marketplace_documentation_status=_status(buckets["marketplace"]),
        branding_asset_status=_status(buckets["branding"]),
        cli_configuration_documentation_status=_status(buckets["cli_config"]),
        telemetry_analytics_documentation_status=_status(buckets["telemetry"]),
        cloud_data_lake_documentation_status=_status(buckets["cloud"]),
        vscode_documentation_status=_status(buckets["vscode"]),
        historical_reference_status=_status(buckets["historical"]),
        deferred_contract_reference_inventory=deferred,
        removed_document_count=removed_docs,
        changed_document_count=changed_docs,
        removed_asset_count=removed_assets,
        checks=list(all_checks),
        defects=list(all_defects),
        blockers=[],
        limitations=limitations,
        total_checks=len(all_checks),
        failed_checks=failed,
        confirmations={
            "schema_1_0_0": True,
            "slice_12_4_not_started": True,
            "no_commit": True,
            "no_tag": True,
            "no_publish": True,
            "no_deploy": True,
            "vscode_only_community_editor": True,
            "assessment_schema_1_2": True,
        },
    )


def run_cursor_documentation_removal_verification(
    *,
    monorepo: Path | None = None,
    output_dir: Path | None = None,
    write_report: bool = True,
    check_determinism_pair: bool = True,
) -> CursorDocumentationRemovalReport:
    root = (monorepo or monorepo_root_from_here()).resolve()
    out = (output_dir or (root / SV123_OUTPUT_RELATIVE)).resolve()
    report = build_report(root)

    if write_report:
        json_path, _ = write_verification_outputs(report, out)
        sc, sd = check_report_safety(json_path)
        report.checks = list(report.checks) + sc
        report.defects = list(report.defects) + sd
        report.total_checks = len(report.checks)
        report.failed_checks = sum(1 for c in report.checks if not c.ok)
        report.verdict = _decide(report.failed_checks, report.defects, report.limitations)
        write_verification_outputs(report, out)

        if check_determinism_pair:
            a_dir, b_dir = out / "_core_a", out / "_core_b"
            a = build_report(root)
            b = build_report(root)
            write_verification_outputs(a, a_dir)
            write_verification_outputs(b, b_dir)
            dc, dd = check_determinism(a_dir / REPORT_JSON, b_dir / REPORT_JSON)
            report.checks = list(report.checks) + dc
            report.defects = list(report.defects) + dd
            report.total_checks = len(report.checks)
            report.failed_checks = sum(1 for c in report.checks if not c.ok)
            report.verdict = _decide(report.failed_checks, report.defects, report.limitations)
            write_verification_outputs(report, out)
            for nested in (a_dir, b_dir):
                if nested.exists():
                    shutil.rmtree(nested)
    return report
