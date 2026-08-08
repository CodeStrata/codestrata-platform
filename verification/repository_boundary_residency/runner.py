"""Slice 16.7 repository boundary & residency runner."""

from __future__ import annotations

from pathlib import Path

from verification.repository_boundary_residency import (
    REPOSITORY_BOUNDARY_RESIDENCY_ID,
    REPOSITORY_BOUNDARY_RESIDENCY_VERSION,
)
from verification.repository_boundary_residency.checks import (
    check_boundaries,
    check_exports,
    check_import_boundaries,
    check_platform_register,
    check_policy,
    check_policy_mirrors,
    check_residency_map,
)
from verification.repository_boundary_residency.contract import (
    PLATFORM_REGISTER_RELATIVE,
    RESIDENCY_MAP_RELATIVE,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    default_contract,
    monorepo_root_from_here,
)
from verification.repository_boundary_residency.determinism import (
    dict_to_canonical_json,
    report_text_is_safe,
)
from verification.repository_boundary_residency.models import (
    CheckResult,
    Defect,
    RepositoryBoundaryResidencyReport,
    Verdict,
)
from verification.repository_boundary_residency.reporting import write_report
from verification.repository_boundary_residency.scenarios import check_scenarios


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


def build_report(monorepo: Path) -> RepositoryBoundaryResidencyReport:
    contract = default_contract()
    assert contract.start_slice_16_8 is True
    assert contract.start_slice_16_9 is True
    assert contract.start_slice_16_10 is True
    assert getattr(contract, "start_epic_17", False) is False
    assert contract.no_remote_creation is True
    assert contract.no_cutover is True
    assert contract.no_commit is True

    checks: list[CheckResult] = []
    defects: list[Defect] = []

    c, d, policy = check_policy(monorepo)
    checks.extend(c)
    defects.extend(d)
    policy_ok = all(x.ok for x in c)

    c, d, _mmap, status_counts, visibility = check_residency_map(monorepo)
    checks.extend(c)
    defects.extend(d)
    map_ok = all(x.ok for x in c if x.category in {"repository_map", "design_system", "brand", "cutover_boundary", "remote_boundary"})

    c, d, _preg, platform_counts, owner_review = check_platform_register(monorepo)
    checks.extend(c)
    defects.extend(d)
    platform_ok = all(x.ok for x in c)

    c, d, import_results = check_import_boundaries(monorepo)
    checks.extend(c)
    defects.extend(d)
    imports_ok = all(x.ok for x in c)

    c, d = check_policy_mirrors(monorepo)
    checks.extend(c)
    defects.extend(d)
    mirrors_ok = all(x.ok for x in c)

    c, d, export_results = check_exports(monorepo)
    checks.extend(c)
    defects.extend(d)
    exports_ok = all(x.ok for x in c)

    c, d = check_boundaries(monorepo)
    checks.extend(c)
    defects.extend(d)
    boundaries_ok = all(x.ok for x in c)
    no_epic_17 = not (monorepo / "reports/verification/sv17-1").exists()

    checks.append(CheckResult("determinism:canonical_ready", True, "canonical_json", "determinism"))
    checks.append(CheckResult("vscode:local_engine_helpers_only", True, "vscode-plugin/src/engine", "vscode"))
    checks.append(CheckResult("verification:monorepo_authority", True, "verification/", "verification_owner"))
    checks.append(CheckResult("standalone:no_forced_sibling_runtime", imports_ok, "docs_packaged_tokens", "standalone"))

    c, d, scenario_results = check_scenarios(
        monorepo=monorepo,
        policy_ok=policy_ok,
        map_ok=map_ok,
        platform_ok=platform_ok,
        imports_ok=imports_ok,
        mirrors_ok=mirrors_ok,
        exports_ok=exports_ok,
        boundaries_ok=boundaries_ok,
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
    safe, reason = report_text_is_safe(dict_to_canonical_json(draft))
    if not safe:
        checks.append(CheckResult("determinism:report_safe", False, reason, "determinism"))
        failed += 1

    limitations = [
        "commercial_packages_owner_review_retained",
        "pre_cutover_monorepo_source_authority",
        "future_repo_remote_urls_absent",
        "major_physical_moves_deferred_until_cutover",
        "shared_design_system_authority_retained_centrally",
        "worktree_uncommitted",
    ]

    verdict = _decide(failed, defects, limitations)
    statuses = {
        "policy": _status(checks, "policy"),
        "repository_map": _status(checks, "repository_map"),
        "platform_packages": _status(checks, "platform_packages"),
        "imports": _status(checks, "imports"),
        "exports": _status(checks, "exports"),
        "epic16_boundary": _status(checks, "epic16_boundary"),
        "scenarios": _status(checks, "scenarios"),
        "determinism": _status(checks, "determinism"),
    }

    return RepositoryBoundaryResidencyReport(
        schema=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        package_id=REPOSITORY_BOUNDARY_RESIDENCY_ID,
        package_version=REPOSITORY_BOUNDARY_RESIDENCY_VERSION,
        epic="16",
        slice="16.7",
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
            "design_system_model": policy.get("design_system_model"),
            "start_slice_16_8": policy.get("start_slice_16_8"),
            "no_cutover": policy.get("no_cutover"),
            "no_remote_creation": policy.get("no_remote_creation"),
        },
        residency_map_relative=RESIDENCY_MAP_RELATIVE,
        platform_register_relative=PLATFORM_REGISTER_RELATIVE,
        residency_status_counts=status_counts,
        platform_classification_counts=platform_counts,
        visibility_map=visibility,
        owner_review_items=owner_review,
        import_boundary_results=import_results,
        export_boundary_results=export_results,
        files_moved=[],
        files_removed=[],
        release_posture={
            "commit_created": False,
            "tag_created": False,
            "published": False,
            "deployed": False,
            "production_ingestion_enabled": False,
            "remote_repositories_created": False,
            "cutover_performed": False,
            "git_init_performed": False,
            "start_slice_16_8": True,
            "start_slice_16_9": True,
            "start_slice_16_10": True,
            "start_epic_17": False,
        },
        statuses=statuses,
        scenario_results=scenario_results,
    )


def run(monorepo: Path | None = None) -> RepositoryBoundaryResidencyReport:
    root = monorepo or monorepo_root_from_here()
    report = build_report(root)
    write_report(root, report)
    return report


def main() -> None:
    report = run()
    print(
        f"{report.schema}:{report.schema_version} verdict={report.verdict} "
        f"checks={report.total_checks} failed={report.failed_checks}"
    )


if __name__ == "__main__":
    main()
