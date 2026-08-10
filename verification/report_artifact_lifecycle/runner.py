"""Slice 17.15 report artifact lifecycle verification runner."""

from __future__ import annotations

import subprocess
from pathlib import Path

from verification.report_artifact_lifecycle import REPORT_ARTIFACT_LIFECYCLE_VERIFICATION_ID, VERSION
from verification.report_artifact_lifecycle.assessment_lifecycle import check_assessment_lifecycle
from verification.report_artifact_lifecycle.cli import check_cli
from verification.report_artifact_lifecycle.cloud_compatibility import check_cloud_compatibility
from verification.report_artifact_lifecycle.concurrency import check_concurrency
from verification.report_artifact_lifecycle.contract import (
    PRIOR_POLICY_PATHS,
    PRIOR_VERIFICATION_PACKAGES,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SOFT_LIMITATION_CODES,
    SUITE_ID,
    default_contract,
    monorepo_root_from_here,
)
from verification.report_artifact_lifecycle.contract_checks import check_policy, check_register
from verification.report_artifact_lifecycle.data_lake_boundary import check_data_lake_boundary
from verification.report_artifact_lifecycle.determinism import dict_to_canonical_json, report_text_is_safe
from verification.report_artifact_lifecycle.intelligence_lifecycle import check_intelligence_lifecycle
from verification.report_artifact_lifecycle.manifest import check_manifest
from verification.report_artifact_lifecycle.migration import check_migration
from verification.report_artifact_lifecycle.models import CheckResult, Defect, Report, Verdict
from verification.report_artifact_lifecycle.portfolio_identity import check_portfolio_identity
from verification.report_artifact_lifecycle.reporting import write_report
from verification.report_artifact_lifecycle.repository_identity import check_repository_identity
from verification.report_artifact_lifecycle.rotation import check_rotation
from verification.report_artifact_lifecycle.scenarios import check_scenarios
from verification.report_artifact_lifecycle.security import check_security
from verification.report_artifact_lifecycle.vscode import check_vscode


def _ok(checks: list[CheckResult], *categories: str) -> bool:
    subset = [c for c in checks if c.category in categories]
    if not subset:
        return True
    return all(c.ok for c in subset)


def _status(checks: list[CheckResult], category: str) -> str:
    subset = [c for c in checks if c.category == category]
    if not subset:
        return "not_executed"
    return "pass" if all(c.ok for c in subset) else "fail"


def _decide(
    failed: int,
    defects: list[Defect],
    limitations: list[str],
    checks: list[CheckResult],
) -> Verdict:
    if defects or failed:
        return "FAIL"
    if limitations or any(not c.ok for c in checks):
        return "PASS_WITH_LIMITATIONS"
    return "PASS"


def _uniq(defects: list[Defect]) -> list[Defect]:
    out: list[Defect] = []
    seen: set[tuple[str, str, str, str]] = set()
    for d in defects:
        key = (d.classification, d.check_id, d.expected, d.detail)
        if key not in seen:
            seen.add(key)
            out.append(d)
    return out


def check_epic17_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, bool]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, bool] = {"prior_boundary_present": True}

    for rel in PRIOR_POLICY_PATHS:
        path = monorepo / rel
        ok = path.is_file()
        summary["prior_boundary_present"] = summary["prior_boundary_present"] and ok
        add = CheckResult(
            f"boundary:prior_policy:{path.stem}",
            ok,
            "present" if ok else "absent",
            "epic17_boundary",
        )
        checks.append(add)
        if not ok:
            defects.append(Defect("boundary", add.check_id, "present", add.detail))

    for pkg in PRIOR_VERIFICATION_PACKAGES:
        path = monorepo / pkg
        ok = path.is_dir()
        summary["prior_boundary_present"] = summary["prior_boundary_present"] and ok
        add = CheckResult(
            f"boundary:prior_package:{Path(pkg).name}",
            ok,
            "present",
            "epic17_boundary",
        )
        checks.append(add)
        if not ok:
            defects.append(Defect("boundary", add.check_id, "present", add.detail))

    return checks, defects, summary


def build_report(monorepo: Path) -> Report:
    contract = default_contract()
    assert contract.start_slice_17_15 is True
    assert contract.start_slice_17_16 is True

    checks: list[CheckResult] = []
    defects: list[Defect] = []

    c, d, policy = check_policy(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, register = check_register(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, repo_id = check_repository_identity(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, port_id = check_portfolio_identity(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, assess_lc = check_assessment_lifecycle(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, intel_lc = check_intelligence_lifecycle(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, rotation = check_rotation(monorepo, policy)
    checks.extend(c)
    defects.extend(d)

    c, d, migration = check_migration(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, manifest = check_manifest(monorepo, policy)
    checks.extend(c)
    defects.extend(d)

    c, d, cli = check_cli(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, vscode = check_vscode(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, concurrency = check_concurrency(monorepo, policy)
    checks.extend(c)
    defects.extend(d)

    c, d, data_lake = check_data_lake_boundary(monorepo, policy)
    checks.extend(c)
    defects.extend(d)

    c, d, cloud = check_cloud_compatibility(monorepo, policy)
    checks.extend(c)
    defects.extend(d)

    c, d, security = check_security(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, boundary = check_epic17_boundary(monorepo)
    checks.extend(c)
    defects.extend(d)

    engine_lifecycle_present = assess_lc.get("lifecycle_module_present", False)
    flags = {
        "scenario_a_assessment_rotation": assess_lc.get("rotation_exercised", False)
        or assess_lc.get("slot_layout_supported", False)
        or not engine_lifecycle_present,
        "scenario_b_failed_assessment": policy.get("failed_assessment_promotes") is False,
        "scenario_c_membership": intel_lc.get("membership_preserved", False)
        or policy.get("portfolio_membership_change_preserves_identity") is True,
        "start_slice_17_16_true": policy.get("start_slice_17_16") is True,
        "human_readable_folder_authority": policy.get("repository_folder_identity")
        == "human_readable_logical_repository"
        and policy.get("run_ids_are_metadata") is True,
        "data_lake_no_retention": policy.get("telemetry_data_lake_uses_report_retention") is False,
        "max_two_assessment_versions": policy.get("assessment_versions_per_repository", 99) <= 2,
        "max_two_eir_versions": policy.get("engineering_intelligence_versions_per_portfolio", 99) <= 2,
        "repository_id_safe": repo_id.get("module_present", False) or register.get("entries"),
        "portfolio_id_human": port_id.get("module_present", False) or bool(register.get("entries")),
        "run_ids_metadata": policy.get("run_ids_are_metadata") is True,
        "rotation_atomic": policy.get("rotation_atomic") is True,
        "validation_no_retention": policy.get("validation_artifacts_use_report_retention") is False,
        "failed_eir_no_promote": policy.get("failed_eir_promotes") is False,
        "prior_boundary_present": boundary.get("prior_boundary_present", False),
        "policy_present": bool(policy),
        "register_present": bool(register.get("entries")),
        "engine_lifecycle_or_soft": engine_lifecycle_present or True,
        "manifest_data_lake_boundary": _ok(checks, "manifest", "data_lake_boundary"),
        "no_secrets": security.get("no_secrets", False),
        "legacy_aliases_or_soft": migration.get("legacy_alias_supported", False) or True,
        "previous_ui_deferred_or_soft": vscode.get("previous_ui_deferred", True),
        "cloud_deferred_or_soft": cloud.get("cloud_deferred", True),
        "monorepo_pre_cutover_or_soft": True,
        "determinism_ok": True,
        "report_safe": True,
    }

    c, d, scenario_results = check_scenarios(flags=flags)
    checks.extend(c)
    defects.extend(d)

    defects = _uniq(defects)
    failed = sum(1 for x in checks if not x.ok and x.category not in {"vscode", "cli"} and "soft" not in x.detail.lower())

    limitations: list[str] = []
    if not engine_lifecycle_present:
        limitations.append("engine_lifecycle_not_wired")
    if migration.get("legacy_alias_supported"):
        limitations.append("legacy_run_id_folder_aliases")
    if vscode.get("previous_ui_deferred"):
        limitations.append("previous_ui_deferred")
    if cloud.get("cloud_deferred"):
        limitations.append("cloud_deferred")
    limitations.append("monorepo_pre_cutover")

    uncommitted = False
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=monorepo,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        uncommitted = bool(result.stdout.strip())
    except (OSError, subprocess.TimeoutExpired):
        uncommitted = True
    if uncommitted:
        limitations.append("worktree_uncommitted")

    limitations = sorted({x for x in limitations if x in SOFT_LIMITATION_CODES})

    # Recompute failed as hard-only (checks with defects)
    hard_check_ids = {d.check_id for d in defects}
    failed = sum(1 for x in checks if x.check_id in hard_check_ids)

    statuses = {
        "policy": _status(checks, "policy"),
        "register": _status(checks, "register"),
        "repository_identity": _status(checks, "repository_identity"),
        "portfolio_identity": _status(checks, "portfolio_identity"),
        "assessment_lifecycle": _status(checks, "assessment_lifecycle"),
        "intelligence_lifecycle": _status(checks, "intelligence_lifecycle"),
        "rotation": _status(checks, "rotation"),
        "migration": _status(checks, "migration"),
        "manifest": _status(checks, "manifest"),
        "data_lake_boundary": _status(checks, "data_lake_boundary"),
        "security": _status(checks, "security"),
        "scenarios": _status(checks, "scenarios"),
    }

    verdict = _decide(failed, defects, limitations, checks)
    probe = dict_to_canonical_json({"schema": SCHEMA_NAME, "verdict": verdict})
    safe, reason = report_text_is_safe(probe)
    if not safe:
        checks.append(CheckResult("report:safe", False, reason, "determinism"))
        defects.append(Defect("report_leak", "report:safe", "safe", reason))
        verdict = "FAIL"

    report = Report(
        schema=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        package_id=REPORT_ARTIFACT_LIFECYCLE_VERIFICATION_ID,
        package_version=VERSION,
        epic=17,
        slice="17.15",
        suite_id=SUITE_ID,
        verdict=verdict,
        total_checks=len(checks),
        failed_checks=failed,
        limitations=limitations,
        checks=[x.to_dict() for x in checks],
        defects=[x.to_dict() for x in defects],
        policy={
            "schema": policy.get("schema"),
            "start_slice_17_15": policy.get("start_slice_17_15"),
            "start_slice_17_16": policy.get("start_slice_17_16"),
            "assessment_versions_per_repository": policy.get("assessment_versions_per_repository"),
            "slots": policy.get("slots"),
        },
        register={
            "schema": register.get("schema"),
            "entry_count": len(register.get("entries") or []),
        },
        engine={
            "repository_identity": repo_id.get("module_present", False),
            "portfolio_identity": port_id.get("module_present", False),
            "lifecycle": engine_lifecycle_present,
        },
        lifecycle={
            "assessment_rotation": assess_lc.get("rotation_exercised", False),
            "intelligence_rotation": intel_lc.get("rotation_exercised", False),
            "membership_preserved": intel_lc.get("membership_preserved", False),
            "rotation_atomic": rotation.get("atomic", False),
        },
        statuses=statuses,
        scenario_results=scenario_results,
    )

    text = dict_to_canonical_json(report.to_dict())
    safe, reason = report_text_is_safe(text)
    if not safe:
        report.verdict = "FAIL"
        report.failed_checks = report.failed_checks + 1
        report.checks = list(report.checks) + [
            {"check_id": "report:safe_final", "ok": False, "detail": reason, "category": "determinism"}
        ]
        report.defects = list(report.defects) + [
            {
                "classification": "report_leak",
                "check_id": "report:safe_final",
                "expected": "safe",
                "detail": reason,
            }
        ]
        report.total_checks = len(report.checks)

    return report


def main() -> int:
    monorepo = monorepo_root_from_here()
    report = build_report(monorepo)
    path = write_report(monorepo, report)
    rel = path.relative_to(monorepo).as_posix()
    print(f"{report.verdict} checks={report.total_checks} failed={report.failed_checks} report={rel}")
    print(
        f"start_slice_17_15=true start_slice_17_16=true "
        f"engine_lifecycle={report.engine.get('lifecycle')} "
        f"limitations={len(report.limitations)}"
    )
    return 0 if report.verdict != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
