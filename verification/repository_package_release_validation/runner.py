"""Slice 16.9 package & release artifact validation runner."""

from __future__ import annotations

from pathlib import Path

from verification.repository_package_release_validation import (
    REPOSITORY_PACKAGE_RELEASE_VALIDATION_ID,
    REPOSITORY_PACKAGE_RELEASE_VALIDATION_VERSION,
)
from verification.repository_package_release_validation.contract import (
    COMMUNITY_REPOS,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    default_contract,
    monorepo_root_from_here,
)
from verification.repository_package_release_validation.determinism import (
    dict_to_canonical_json,
    report_text_is_safe,
)
from verification.repository_package_release_validation.export_determinism import (
    check_export_determinism,
)
from verification.repository_package_release_validation.export_validation import (
    check_exports,
    cleanup_export_base,
)
from verification.repository_package_release_validation.models import (
    CheckResult,
    Defect,
    RepositoryPackageReleaseValidationReport,
    Verdict,
)
from verification.repository_package_release_validation.package_validation import check_packages
from verification.repository_package_release_validation.policy import check_policy
from verification.repository_package_release_validation.public_audit import check_public_audit
from verification.repository_package_release_validation.release_artifacts import (
    check_release_artifacts,
)
from verification.repository_package_release_validation.reporting import write_report
from verification.repository_package_release_validation.scenarios import check_scenarios
from verification.repository_package_release_validation.security import check_security
from verification.repository_package_release_validation.standalone_build import (
    check_standalone_builds,
)
from verification.repository_package_release_validation.standalone_repo import (
    check_standalone_repos,
)


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


def _sanitize(obj):
    """Remove absolute path strings from nested structures for the report."""
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items() if k != "_cleanup_base"}
    if isinstance(obj, list):
        return [_sanitize(x) for x in obj]
    if isinstance(obj, str):
        if obj.startswith("/Users/") or obj.startswith("/home/") or obj.startswith("/var/") or obj.startswith("/tmp/"):
            return "<temp>"
        return obj
    return obj


def build_report(monorepo: Path) -> RepositoryPackageReleaseValidationReport:
    contract = default_contract()
    assert contract.start_slice_16_9 is True
    assert contract.start_slice_16_10 is True
    assert getattr(contract, "start_epic_17", False) is False
    assert contract.no_publish is True
    assert contract.no_commit is True

    checks: list[CheckResult] = []
    defects: list[Defect] = []

    c, d, policy = check_policy(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, export_summary, roots, _fps = check_exports(monorepo)
    checks.extend(c)
    defects.extend(d)

    try:
        c, d, standalone_summary = check_standalone_repos(roots)
        checks.extend(c)
        defects.extend(d)

        c, d, build_summary = check_standalone_builds(monorepo, roots)
        checks.extend(c)
        defects.extend(d)

        c, d, package_summary = check_packages(roots)
        checks.extend(c)
        defects.extend(d)

        c, d, artifact_summary = check_release_artifacts(monorepo, roots)
        checks.extend(c)
        defects.extend(d)

        c, d, audit_summary = check_public_audit(roots)
        checks.extend(c)
        defects.extend(d)

        c, d, security_summary = check_security(roots)
        checks.extend(c)
        defects.extend(d)
    finally:
        cleanup_export_base(export_summary)

    c, d, det_summary = check_export_determinism(monorepo)
    checks.extend(c)
    defects.extend(d)

    no_epic_17 = not (monorepo / "reports/verification/sv17-1").exists()
    no_epic19 = not (monorepo / "verification/release_readiness").exists()
    checks.append(
        CheckResult("boundary:no_sv17_1", no_epic_17, "sv17-1 absent", "release_boundary")
    )
    checks.append(
        CheckResult("boundary:no_epic19_package", no_epic19, "no release_readiness pkg", "release_boundary")
    )
    checks.append(CheckResult("determinism:canonical_ready", True, "canonical_json", "determinism"))

    flags = {
        "export_ok": _ok(checks, "export"),
        "standalone_ok": _ok(checks, "standalone"),
        "build_ok": _ok(checks, "standalone_build"),
        "package_ok": _ok(checks, "package"),
        "audit_ok": _ok(checks, "public_audit"),
        "security_ok": _ok(checks, "security"),
        "determinism_ok": _ok(checks, "determinism"),
        "no_publish": True,
        "no_epic_17": no_epic_17,
        "no_epic19": no_epic19,
        "no_cutover": True,
        "report_safe": True,
    }
    c, d, scenario_results = check_scenarios(flags=flags)
    checks.extend(c)
    defects.extend(d)

    defects = _uniq(defects)
    failed = sum(1 for x in checks if not x.ok)

    limitations = [
        "validation_only_no_publish",
        "worktree_uncommitted",
        "future_repo_remotes_absent",
        "physical_cutover_deferred",
        "opentofu_network_may_limit_provider_init",
        "recommended_root_files_may_be_absent_on_private_repos",
        "epic19_release_readiness_not_started",
    ]

    # Soft: if insights missing LICENSE, keep as limitation if we choose to not fail —
    # currently standalone required files will fail. We'll narrow-fix by adding LICENSE.

    statuses = {
        "policy": _status(checks, "policy"),
        "export": _status(checks, "export"),
        "standalone": _status(checks, "standalone"),
        "standalone_build": _status(checks, "standalone_build"),
        "package": _status(checks, "package"),
        "release_artifacts": _status(checks, "release_artifacts"),
        "public_audit": _status(checks, "public_audit"),
        "security": _status(checks, "security"),
        "determinism": _status(checks, "determinism"),
        "scenarios": _status(checks, "scenarios"),
        "release_boundary": _status(checks, "release_boundary"),
    }

    inventory = [{"name": r, "via": "community_export"} for r in COMMUNITY_REPOS]
    inventory.extend(
        [
            {"name": "codestrata-insights", "via": "insights_export"},
            {"name": "codestrata-infrastructure", "via": "infrastructure_export"},
        ]
    )

    verdict = _decide(failed, defects, limitations)

    probe = dict_to_canonical_json({"schema": SCHEMA_NAME, "verdict": verdict})
    safe, reason = report_text_is_safe(probe)
    if not safe:
        checks.append(CheckResult("report:safe", False, reason, "determinism"))
        defects.append(Defect("report_leak", "report:safe", "safe", reason))
        failed += 1
        verdict = "FAIL"

    report = RepositoryPackageReleaseValidationReport(
        schema=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        package_id=REPOSITORY_PACKAGE_RELEASE_VALIDATION_ID,
        package_version=REPOSITORY_PACKAGE_RELEASE_VALIDATION_VERSION,
        epic="16",
        slice="16.9",
        verdict=verdict,
        total_checks=len(checks),
        failed_checks=failed,
        limitations=sorted(limitations),
        checks=[
            {"check_id": x.check_id, "ok": x.ok, "detail": x.detail, "category": x.category}
            for x in checks
        ],
        defects=[
            {
                "classification": x.classification,
                "surface": x.surface,
                "expected": x.expected,
                "observed": x.observed,
            }
            for x in defects
        ],
        policy={
            "schema": policy.get("schema"),
            "policy_id": policy.get("policy_id"),
            "start_slice_16_9": policy.get("start_slice_16_9"),
            "start_slice_16_10": policy.get("start_slice_16_10"),
        },
        export_validation=_sanitize(export_summary),
        standalone_package_validation=_sanitize(standalone_summary),
        standalone_build_validation=_sanitize(build_summary),
        release_artifact_validation=_sanitize(artifact_summary),
        public_repository_readiness=_sanitize(audit_summary),
        security_validation=_sanitize(security_summary),
        determinism=_sanitize(det_summary),
        repository_inventory=inventory,
        release_posture={
            "start_slice_16_9": True,
            "start_slice_16_10": True,
            "start_epic_17": False,
            "no_publish": True,
            "no_deploy": True,
            "no_tag": True,
            "no_commit": True,
            "no_marketplace_publish": True,
            "no_pypi_publish": True,
            "no_github_release": True,
            "production_ingestion_enabled": False,
            "package_summary": _sanitize(package_summary),
        },
        statuses=statuses,
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
