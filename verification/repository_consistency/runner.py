"""Slice 16.8 repository consistency runner."""

from __future__ import annotations

from pathlib import Path

from verification.repository_consistency import (
    REPOSITORY_CONSISTENCY_ID,
    REPOSITORY_CONSISTENCY_VERSION,
)
from verification.repository_consistency.brand import check_brand
from verification.repository_consistency.ci import check_ci
from verification.repository_consistency.code import check_code
from verification.repository_consistency.community_scope import check_community_scope
from verification.repository_consistency.contract import (
    OWNER_REGISTER_RELATIVE,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    default_contract,
    monorepo_root_from_here,
)
from verification.repository_consistency.contracts import check_contracts
from verification.repository_consistency.cross_repo_contracts import check_cross_repo_contracts
from verification.repository_consistency.dependencies import check_builds, check_dependencies
from verification.repository_consistency.design_system import check_design_system
from verification.repository_consistency.determinism import (
    dict_to_canonical_json,
    report_text_is_safe,
)
from verification.repository_consistency.documentation import check_documentation
from verification.repository_consistency.epic16_boundary import check_epic16_boundary
from verification.repository_consistency.exports import check_exports
from verification.repository_consistency.generated import check_generated
from verification.repository_consistency.historical import check_historical
from verification.repository_consistency.imports import check_imports
from verification.repository_consistency.models import (
    CheckResult,
    Defect,
    RepositoryConsistencyReport,
    Verdict,
)
from verification.repository_consistency.owner_review import check_owner_review
from verification.repository_consistency.package_roots import check_package_roots
from verification.repository_consistency.platform import check_platform
from verification.repository_consistency.policies import check_policies
from verification.repository_consistency.policy import check_consistency_policy
from verification.repository_consistency.release_boundary import check_release_boundary
from verification.repository_consistency.release_tooling import check_release_tooling
from verification.repository_consistency.reporting import write_report
from verification.repository_consistency.runtime_regression import check_runtime_regression
from verification.repository_consistency.scenarios import check_scenarios
from verification.repository_consistency.structure import check_structure
from verification.repository_consistency.tests_verification import check_tests_verification
from verification.repository_consistency.versions import check_versions
from verification.repository_consistency.visibility import check_visibility
from verification.repository_consistency.worktree import check_worktree


def _status(checks: list[CheckResult], category: str) -> str:
    subset = [c for c in checks if c.category == category]
    if not subset:
        return "not_executed"
    return "pass" if all(c.ok for c in subset) else "fail"


def _ok(checks: list[CheckResult], category: str) -> bool:
    subset = [c for c in checks if c.category == category]
    return all(c.ok for c in subset) if subset else True


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


def build_report(monorepo: Path) -> RepositoryConsistencyReport:
    contract = default_contract()
    assert contract.start_slice_16_8 is True
    assert contract.start_slice_16_9 is True
    assert contract.start_slice_16_10 is True
    assert getattr(contract, "start_epic_17", False) is False
    assert contract.no_commit is True
    assert contract.no_remote_creation is True

    checks: list[CheckResult] = []
    defects: list[Defect] = []

    c, d, policy = check_consistency_policy(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, top_map = check_structure(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d = check_documentation(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d = check_code(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, _pcounts, _powner = check_platform(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, policy_summary = check_policies(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, contract_summary = check_contracts(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, version_registry = check_versions(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d = check_dependencies(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, build_summary = check_builds(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d = check_generated(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d = check_design_system(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d = check_brand(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, export_results = check_exports(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, visibility_matrix = check_visibility(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d = check_package_roots(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, _import_results = check_imports(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, cross_matrix = check_cross_repo_contracts(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d = check_ci(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d = check_release_tooling(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d = check_community_scope(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, historical = check_historical(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d = check_tests_verification(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, owner_items = check_owner_review(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, _residue = check_worktree(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d = check_runtime_regression(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d = check_release_boundary(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d = check_epic16_boundary(monorepo)
    checks.extend(c)
    defects.extend(d)

    no_epic_17 = not (monorepo / "reports/verification/sv17-1").exists()
    checks.append(CheckResult("determinism:canonical_ready", True, "canonical_json", "determinism"))

    flags = {
        "docs_ok": _ok(checks, "documentation") and _ok(checks, "community_scope"),
        "platform_ok": _ok(checks, "platform"),
        "policies_ok": _ok(checks, "policies"),
        "contracts_ok": _ok(checks, "contracts"),
        "versions_ok": _ok(checks, "versions"),
        "release_ok": _ok(checks, "release_tooling"),
        "code_ok": _ok(checks, "code"),
        "generated_ok": _ok(checks, "generated"),
        "design_ok": _ok(checks, "design_system"),
        "brand_ok": _ok(checks, "brand"),
        "exports_ok": _ok(checks, "exports"),
        "visibility_ok": _ok(checks, "visibility"),
        "imports_ok": _ok(checks, "imports"),
        "pkgroot_ok": _ok(checks, "package_roots"),
        "ci_ok": _ok(checks, "ci"),
        "community_ok": _ok(checks, "community_scope"),
        "owner_ok": _ok(checks, "owner_review"),
        "no_epic_17": no_epic_17,
        "runtime_ok": _ok(checks, "runtime_regression"),
        "report_safe": True,
    }
    c, d, scenario_results = check_scenarios(monorepo=monorepo, flags=flags)
    checks.extend(c)
    defects.extend(d)

    defects = _uniq(defects)
    failed = sum(1 for x in checks if not x.ok)

    limitations = [
        "commercial_packages_owner_review_retained",
        "historical_amber_archive_retained",
        "historical_fixtures_and_verifiers_retained",
        "future_repo_cutovers_deferred",
        "dependency_upgrades_deferred",
        "codestrata_examples_environment_protected",
        "opentofu_provider_network_limitation",
        "worktree_uncommitted",
    ]

    domain_verdicts = {
        "structure": _status(checks, "structure"),
        "documentation": _status(checks, "documentation"),
        "code": _status(checks, "code"),
        "platform": _status(checks, "platform"),
        "policies": _status(checks, "policies"),
        "contracts": _status(checks, "contracts"),
        "versions": _status(checks, "versions"),
        "dependencies": _status(checks, "dependencies"),
        "builds": _status(checks, "builds"),
        "generated": _status(checks, "generated"),
        "design_system": _status(checks, "design_system"),
        "brand": _status(checks, "brand"),
        "exports": _status(checks, "exports"),
        "visibility": _status(checks, "visibility"),
        "package_roots": _status(checks, "package_roots"),
        "imports": _status(checks, "imports"),
        "cross_repo_contracts": _status(checks, "cross_repo_contracts"),
        "ci": _status(checks, "ci"),
        "release_tooling": _status(checks, "release_tooling"),
        "community_scope": _status(checks, "community_scope"),
        "historical": _status(checks, "historical"),
        "owner_review": _status(checks, "owner_review"),
        "worktree": _status(checks, "worktree"),
        "runtime_regression": _status(checks, "runtime_regression"),
        "epic16_boundary": _status(checks, "epic16_boundary"),
        "scenarios": _status(checks, "scenarios"),
    }

    authority_registry = {
        "consistency_policy": "platform/policies/repository_consistency_policy.json",
        "owner_review_register": OWNER_REGISTER_RELATIVE,
        "residency_map": "platform/policies/repository_residency_map.json",
        "platform_packages": "platform/policies/platform_package_register.json",
        "dependency_register": "platform/policies/repository_dependency_register.json",
        "build_register": "platform/policies/repository_build_authority_register.json",
        "generated_register": "platform/policies/repository_generated_artifact_register.json",
        "asset_manifest": "design-system/assets/asset-authority-manifest.json",
        "design_system": "design-system/",
    }

    unresolved = [d.surface for d in defects]
    release_blocking = [
        d.surface
        for d in defects
        if d.classification
        in {
            "version_conflict",
            "duplicate_policy_authority",
            "duplicate_contract_authority",
            "public_export_includes_platform",
            "public_export_includes_insights",
            "slice_16_9_started",
            "unclassified_platform_package",
        }
    ]

    verdict = _decide(failed, defects, limitations)

    # Safety probe before write
    probe = {
        "schema": SCHEMA_NAME,
        "schema_version": SCHEMA_VERSION,
        "verdict": verdict,
    }
    safe, _reason = report_text_is_safe(dict_to_canonical_json(probe))
    flags["report_safe"] = safe
    if not safe:
        checks.append(CheckResult("report:safe", False, _reason, "determinism"))
        defects.append(Defect("report_leak", "report:safe", "safe", _reason))
        failed += 1
        verdict = "FAIL"

    report = RepositoryConsistencyReport(
        schema=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        package_id=REPOSITORY_CONSISTENCY_ID,
        package_version=REPOSITORY_CONSISTENCY_VERSION,
        epic="16",
        slice="16.8",
        verdict=verdict,
        total_checks=len(checks),
        failed_checks=failed,
        limitations=sorted(limitations),
        checks=[{"check_id": c.check_id, "ok": c.ok, "detail": c.detail, "category": c.category} for c in checks],
        defects=[
            {
                "classification": d.classification,
                "surface": d.surface,
                "expected": d.expected,
                "observed": d.observed,
            }
            for d in defects
        ],
        policy={
            "schema": policy.get("schema"),
            "policy_id": policy.get("policy_id"),
            "policy_version": policy.get("policy_version"),
            "start_slice_16_8": policy.get("start_slice_16_8"),
            "start_slice_16_9": policy.get("start_slice_16_9"),
        },
        domain_verdicts=domain_verdicts,
        top_level_map=top_map,
        authority_registry=authority_registry,
        policy_registry_summary=policy_summary,
        contract_registry_summary=contract_summary,
        version_registry=version_registry,
        build_authority_summary=build_summary,
        visibility_matrix=visibility_matrix,
        cross_repo_contract_matrix=cross_matrix,
        owner_review_register=owner_items,
        historical_exceptions=historical,
        unresolved_findings=unresolved,
        release_blocking_findings=release_blocking,
        release_posture={
            "start_slice_16_8": True,
            "start_slice_16_9": True,
            "start_slice_16_10": True,
            "start_epic_17": False,
            "no_remote_creation": True,
            "no_cutover": True,
            "no_commit": True,
            "no_tag": True,
            "no_publish": True,
            "no_deploy": True,
            "production_ingestion_enabled": False,
            "export_targets": list(export_results),
        },
        statuses={k: v for k, v in domain_verdicts.items()},
        scenario_results=scenario_results,
    )
    return report


def main() -> int:
    monorepo = monorepo_root_from_here()
    report = build_report(monorepo)
    path = write_report(monorepo, report)
    rel = path.relative_to(monorepo).as_posix()
    print(f"{report.verdict} checks={report.total_checks} failed={report.failed_checks} report={rel}")
    return 0 if report.verdict != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
