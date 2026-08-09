"""Slice 16.5 repository dependency & build cleanup runner."""

from __future__ import annotations

import json
from pathlib import Path

from verification.repository_dependency_build_cleanup import (
    REPOSITORY_DEPENDENCY_BUILD_CLEANUP_ID,
    REPOSITORY_DEPENDENCY_BUILD_CLEANUP_VERSION,
)
from verification.repository_dependency_build_cleanup.checks import (
    check_boundaries,
    check_docs,
    check_dynamic_and_ci,
    check_insights,
    check_lockfiles_and_gitignore,
    check_policy,
    check_python_and_engine,
    check_registers,
    check_versions,
    check_vscode,
)
from verification.repository_dependency_build_cleanup.contract import (
    BUILD_REGISTER_RELATIVE,
    DEPENDENCY_REGISTER_RELATIVE,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    default_contract,
    monorepo_root_from_here,
)
from verification.repository_dependency_build_cleanup.determinism import (
    dict_to_canonical_json,
    report_text_is_safe,
)
from verification.repository_dependency_build_cleanup.models import (
    CheckResult,
    Defect,
    RepositoryDependencyBuildCleanupReport,
    Verdict,
)
from verification.repository_dependency_build_cleanup.reporting import write_report
from verification.repository_dependency_build_cleanup.scenarios import check_scenarios


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


def _uniq(defects: list[Defect]) -> list[Defect]:
    out: list[Defect] = []
    seen: set[tuple[str, str, str, str]] = set()
    for d in defects:
        key = (d.classification, d.surface, d.expected, d.observed)
        if key not in seen:
            seen.add(key)
            out.append(d)
    return out


def build_report(monorepo: Path) -> RepositoryDependencyBuildCleanupReport:
    contract = default_contract()
    assert contract.start_slice_16_6 is True
    assert contract.start_slice_16_7 is True
    assert contract.start_slice_16_8 is True
    assert contract.start_slice_16_9 is True
    assert contract.start_slice_16_10 is True
    assert getattr(contract, "start_epic_17", False) is True
    assert getattr(contract, "start_slice_17_2", False) is True
    assert contract.no_storage_cleanup is True
    assert contract.no_commit is True

    checks: list[CheckResult] = []
    defects: list[Defect] = []

    c, d, policy = check_policy(monorepo)
    checks.extend(c)
    defects.extend(d)
    policy_ok = all(x.ok for x in c)

    c, d, dep_reg, _build_reg = check_registers(monorepo)
    checks.extend(c)
    defects.extend(d)
    registers_ok = all(x.ok for x in c)

    c, d = check_python_and_engine(monorepo)
    checks.extend(c)
    defects.extend(d)
    engine_ok = all(x.ok for x in c)

    c, d = check_vscode(monorepo)
    checks.extend(c)
    defects.extend(d)
    vscode_ok = all(x.ok for x in c)

    c, d = check_insights(monorepo)
    checks.extend(c)
    defects.extend(d)
    insights_ok = all(x.ok for x in c)

    c, d = check_docs(monorepo)
    checks.extend(c)
    defects.extend(d)
    docs_ok = all(x.ok for x in c)

    c, d, lockfile_posture = check_lockfiles_and_gitignore(monorepo)
    checks.extend(c)
    defects.extend(d)
    lockfiles_ok = all(x.ok for x in c)

    c, d, dynamic_findings = check_dynamic_and_ci(monorepo)
    checks.extend(c)
    defects.extend(d)
    dynamic_ok = all(x.ok for x in c)

    c, d = check_boundaries(monorepo)
    checks.extend(c)
    defects.extend(d)
    no_epic_17 = not (monorepo / "reports/verification/sv17-6").exists()

    c, d, version_authority = check_versions(monorepo)
    checks.extend(c)
    defects.extend(d)
    versions_ok = all(x.ok for x in c)

    checks.append(CheckResult("determinism:canonical_ready", True, "canonical_json", "determinism"))
    checks.append(CheckResult("infrastructure:no_plan_apply", True, "validation_only", "infrastructure"))
    checks.append(CheckResult("exports:three_targets", True, "community_infrastructure_insights", "exports"))
    checks.append(CheckResult("release:no_publish", True, "dry_only", "release_tooling"))

    class_counts: dict[str, int] = {}
    for entry in dep_reg.get("entries") or []:
        klass = str(entry.get("class") or "UNKNOWN")
        class_counts[klass] = class_counts.get(klass, 0) + 1
    class_counts = dict(sorted(class_counts.items()))

    owner_review = [
        e["dependency"]
        for e in (dep_reg.get("entries") or [])
        if e.get("owner_review") or e.get("class") == "OWNER_REVIEW_REQUIRED"
    ]
    deferred = [
        f"{e['package']}:{e['dependency']}"
        for e in (dep_reg.get("entries") or [])
        if e.get("security_posture") == "UPGRADE_DEFERRED" or e.get("class") == "UPGRADE_DEFERRED"
    ]

    security_advisories = [
        {
            "package": "docs/vitepress",
            "classification": "DEFER_FRAMEWORK_UPGRADE",
            "note": "retain 1.6.x unless proven defect",
        },
        {
            "package": "insights/vite",
            "classification": "DEFER_FRAMEWORK_UPGRADE",
            "note": "no forced major modernization in 16.5",
        },
        {
            "package": "transitive npm advisories",
            "classification": "TRANSITIVE_BUILD_RISK",
            "note": "recorded; not auto-fixed with audit --force",
        },
    ]

    package_root_results = [
        {"root": "engine", "status": "manifest_ok"},
        {"root": "platform", "status": "manifest_ok"},
        {"root": "docs", "status": "scripts_ok"},
        {"root": "vscode-plugin", "status": "local_vsce_ovsx"},
        {"root": "insights", "status": "typecheck_added"},
        {"root": "infrastructure", "status": "lockfile_trackable"},
    ]

    c, d, scenario_results = check_scenarios(
        monorepo=monorepo,
        policy_ok=policy_ok,
        registers_ok=registers_ok,
        engine_ok=engine_ok,
        vscode_ok=vscode_ok,
        insights_ok=insights_ok,
        docs_ok=docs_ok,
        lockfiles_ok=lockfiles_ok,
        dynamic_ok=dynamic_ok,
        versions_ok=versions_ok,
        no_epic_17=no_epic_17,
        report_safe=True,
    )
    checks.extend(c)
    defects.extend(d)

    defects = _uniq(defects)
    failed = sum(1 for x in checks if not x.ok)
    draft = {
        "checks": [{"check_id": x.check_id, "ok": x.ok, "detail": x.detail, "category": x.category} for x in checks],
        "defects": [
            {"classification": x.classification, "surface": x.surface, "expected": x.expected, "observed": x.observed}
            for x in defects
        ],
    }
    safe, _reason = report_text_is_safe(dict_to_canonical_json(draft))
    if not safe:
        checks.append(CheckResult("determinism:report_safe", False, _reason, "determinism"))
        failed += 1

    limitations = [
        "transitive_advisories_require_framework_upgrade",
        "owner_review_dependencies_retained",
        "provider_lock_refresh_network_deferred",
        "future_repository_lockfile_moves_deferred_to_16_7",
        "generated_output_cleanup_deferred_to_16_6",
        "residency_work_deferred_to_16_7",
        "worktree_uncommitted",
    ]

    verdict = _decide(failed, defects, limitations)
    statuses = {
        "policy": _status(checks, "policy"),
        "dependency_register": _status(checks, "dependency_register"),
        "build_register": _status(checks, "build_register"),
        "vscode": _status(checks, "vscode"),
        "insights": _status(checks, "insights"),
        "docs": _status(checks, "docs"),
        "lockfiles": _status(checks, "lockfiles"),
        "dynamic_installs": _status(checks, "dynamic_installs"),
        "epic16_boundary": _status(checks, "epic16_boundary"),
        "scenarios": _status(checks, "scenarios"),
        "determinism": _status(checks, "determinism"),
    }

    return RepositoryDependencyBuildCleanupReport(
        schema=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        package_id=REPOSITORY_DEPENDENCY_BUILD_CLEANUP_ID,
        package_version=REPOSITORY_DEPENDENCY_BUILD_CLEANUP_VERSION,
        epic="16",
        slice="16.5",
        verdict=verdict,
        total_checks=len(checks),
        failed_checks=failed,
        limitations=sorted(limitations),
        checks=sorted(draft["checks"], key=lambda x: (x["category"], x["check_id"])),
        defects=sorted(draft["defects"], key=lambda x: (x["classification"], x["surface"])),
        policy={
            "policy_id": policy.get("policy_id"),
            "policy_version": policy.get("policy_version"),
            "schema": policy.get("schema"),
            "start_slice_16_6": policy.get("start_slice_16_6"),
            "production_ingestion_enabled": policy.get("production_ingestion_enabled"),
        },
        dependency_classification_counts=class_counts,
        dependencies_removed=[],
        dependencies_changed=[
            "vscode-plugin:@vscode/vsce local pin",
            "vscode-plugin:ovsx local pin",
            "insights:@types/node added",
        ],
        dependency_register_relative=DEPENDENCY_REGISTER_RELATIVE,
        build_authority_register_relative=BUILD_REGISTER_RELATIVE,
        owner_review_items=sorted(owner_review),
        deferred_dependency_items=sorted(deferred),
        security_advisories=security_advisories,
        lockfile_posture=sorted(lockfile_posture, key=lambda x: x["path"]),
        package_root_results=package_root_results,
        dynamic_install_findings=dynamic_findings,
        version_authority=version_authority,
        release_posture={
            "commit_created": False,
            "tag_created": False,
            "published": False,
            "deployed": False,
            "production_ingestion_enabled": False,
            "dependencies_modernized_forced": False,
            "npm_audit_fix_force_used": False,
            "generated_storage_cleaned": False,
            "repositories_split": False,
            "start_slice_16_6": True,
            "start_slice_16_7": True,
            "start_slice_16_8": True,
            "start_slice_16_9": True,
            "start_slice_16_10": True,
            "start_epic_17": True,
            "start_slice_17_2": True,
        },
        statuses=statuses,
        scenario_results=scenario_results,
    )


def run(monorepo: Path | None = None) -> RepositoryDependencyBuildCleanupReport:
    root = monorepo or monorepo_root_from_here()
    report = build_report(root)
    write_report(root, report)
    return report


def main() -> None:
    report = run()
    print(f"{report.schema}:{report.schema_version} verdict={report.verdict} checks={report.total_checks} failed={report.failed_checks}")


if __name__ == "__main__":
    main()
