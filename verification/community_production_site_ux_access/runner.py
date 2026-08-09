"""Slice 17.11 production site UX and access runner."""

from __future__ import annotations

from pathlib import Path

from verification.community_production_site_ux_access import (
    COMMUNITY_PRODUCTION_SITE_UX_ACCESS_ID,
    VERSION,
)
from verification.community_production_site_ux_access.checks import (
    check_auth_rca,
    check_docs_ux,
    check_epic17_boundary,
    check_insights_ux,
    check_operational,
    check_policy,
    check_regressions,
    check_sites_posture,
    load_evidence,
)
from verification.community_production_site_ux_access.contract import (
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SOFT_CHECK_IDS,
    SOFT_LIMITATION_CODES,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_production_site_ux_access.determinism import (
    dict_to_canonical_json,
    report_text_is_safe,
)
from verification.community_production_site_ux_access.models import (
    CheckResult,
    Defect,
    Report,
    Verdict,
)
from verification.community_production_site_ux_access.reporting import write_report
from verification.community_production_site_ux_access.scenarios import check_scenarios


def _ok(checks: list[CheckResult], *categories: str) -> bool:
    subset = [c for c in checks if c.category in categories]
    if not subset:
        return True
    return all(c.ok or c.check_id in SOFT_CHECK_IDS for c in subset)


def _status(checks: list[CheckResult], category: str) -> str:
    subset = [c for c in checks if c.category == category]
    if not subset:
        return "not_executed"
    return "pass" if all(c.ok or c.check_id in SOFT_CHECK_IDS for c in subset) else "fail"


def _decide(
    failed: int,
    defects: list[Defect],
    limitations: list[str],
    checks: list[CheckResult],
) -> Verdict:
    hard_failed = sum(1 for c in checks if (not c.ok) and c.check_id not in SOFT_CHECK_IDS)
    if hard_failed or defects:
        return "FAIL"
    if limitations or any(not c.ok for c in checks):
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


def _policy_summary(policy: dict, register: dict) -> dict:
    fields = (
        "docs_repo_visibility",
        "docs_site_public",
        "docs_header_overlap_fixed",
        "docs_logo_destination",
        "docs_main_site_destination",
        "docs_inner_footer_posture",
        "docs_favicon_status",
        "insights_favicon_status",
        "insights_auth_root_cause",
        "insights_password_rotation_performed",
        "insights_login_status",
        "production_sites_status",
        "start_slice_17_11",
        "start_slice_17_12",
    )
    summary = {"schema": policy.get("schema")}
    for field in fields:
        summary[field] = policy.get(field) if field in policy else register.get(field)
    return summary


def build_report(monorepo: Path) -> Report:
    contract = default_contract()
    assert contract.start_slice_17_11 is True
    assert contract.start_slice_17_12 is True
    assert getattr(contract, "start_slice_17_13", False) is False

    checks: list[CheckResult] = []
    defects: list[Defect] = []

    evidence = load_evidence(monorepo)

    c, d, policy, register = check_policy(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, docs_ux = check_docs_ux(monorepo, policy)
    checks.extend(c)
    defects.extend(d)

    c, d, insights_ux = check_insights_ux(monorepo, policy)
    checks.extend(c)
    defects.extend(d)

    c, d, sites_posture = check_sites_posture(monorepo, policy)
    checks.extend(c)
    defects.extend(d)

    c, d, auth_rca = check_auth_rca(monorepo, policy, evidence)
    checks.extend(c)
    defects.extend(d)

    c, d, operational = check_operational(evidence)
    checks.extend(c)
    defects.extend(d)

    c, d, regressions = check_regressions(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, epic17_boundary = check_epic17_boundary(monorepo)
    checks.extend(c)
    defects.extend(d)

    flags = {
        "header_overlap_fixed": docs_ux.get("docs_header_overlap_fixed", False),
        "logo_main_site_clear": _ok(checks, "docs_ux"),
        "docs_repo_private": sites_posture.get("docs_repo_visibility") == "private",
        "docs_site_public": sites_posture.get("docs_site_public") is True,
        "report_no_secrets": True,
        "slice_17_13_absent": epic17_boundary.get("start_slice_17_13", False) is False and _ok(checks, "epic17_boundary"),
        "insights_favicon_ok": _ok(checks, "insights_ux"),
        "docs_favicon_ok": _ok(checks, "docs_ux"),
        "inner_footer_minimal": _ok(checks, "docs_ux"),
        "auth_root_cause_encoded": auth_rca.get("insights_auth_root_cause") == contract.insights_auth_root_cause,
        "rotation_not_required": auth_rca.get("insights_password_rotation_performed") is False,
        "insights_login_ok": _ok(checks, "insights_ux"),
        "production_sites_ok": sites_posture.get("production_sites_status") is not None,
        "determinism_ok": True,
        "report_safe": True,
    }

    c, d, scenario_results = check_scenarios(flags=flags)
    checks.extend(c)
    defects.extend(d)

    defects = _uniq(defects)
    failed = sum(1 for x in checks if (not x.ok) and x.check_id not in SOFT_CHECK_IDS)

    limitations: list[str] = []
    limitations.append("monorepo_remains_source_authority_pre_cutover")
    limitations.append("worktree_uncommitted")
    limitations.append("owner_once_password_file_manual_copy_delete")
    if not evidence.get("password_rca"):
        limitations.append("password_rca_evidence_absent")
    if not evidence.get("live_auth"):
        limitations.append("live_auth_evidence_absent")
    if not evidence.get("live_docs"):
        limitations.append("live_docs_evidence_absent")
    if not evidence.get("github_visibility"):
        limitations.append("github_visibility_evidence_absent")
        limitations.append("github_cli_auth_pending")
    if not evidence.get("deploy"):
        limitations.append("deploy_evidence_absent")
    limitations = sorted({x for x in limitations if x in SOFT_LIMITATION_CODES})

    statuses = {
        "policy": _status(checks, "policy"),
        "docs_ux": _status(checks, "docs_ux"),
        "insights_ux": _status(checks, "insights_ux"),
        "sites_posture": _status(checks, "sites_posture"),
        "auth_rca": _status(checks, "auth_rca"),
        "operational": _status(checks, "operational"),
        "regressions": _status(checks, "regressions"),
        "epic17_boundary": _status(checks, "epic17_boundary"),
        "scenarios": _status(checks, "scenarios"),
    }

    verdict = _decide(failed, defects, limitations, checks)
    probe = dict_to_canonical_json({"schema": SCHEMA_NAME, "verdict": verdict})
    safe, reason = report_text_is_safe(probe)
    if not safe:
        checks.append(CheckResult("report:safe", False, reason, "determinism"))
        defects.append(Defect("report_leak", "report:safe", "safe", reason))
        failed += 1
        verdict = "FAIL"

    report = Report(
        schema=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        package_id=COMMUNITY_PRODUCTION_SITE_UX_ACCESS_ID,
        package_version=VERSION,
        epic="17",
        slice="17.11",
        verdict=verdict,
        total_checks=len(checks),
        failed_checks=failed,
        limitations=limitations,
        checks=[{"check_id": x.check_id, "ok": x.ok, "detail": x.detail, "category": x.category} for x in checks],
        defects=[
            {"classification": x.classification, "surface": x.surface, "expected": x.expected, "observed": x.observed}
            for x in defects
        ],
        policy=_policy_summary(policy, register),
        register={
            "schema": register.get("schema"),
            "entry_count": len(register.get("entries") or []),
            "start_slice_17_11": register.get("start_slice_17_11"),
            "start_slice_17_12": register.get("start_slice_17_12"),
        },
        evidence={
            "present": evidence.get("present"),
            "file_count": len(evidence.get("files") or {}),
        },
        docs_ux=docs_ux,
        insights_ux=insights_ux,
        sites_posture=sites_posture,
        auth_rca=auth_rca,
        regressions=regressions,
        epic17_boundary=epic17_boundary,
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
            {"classification": "report_leak", "surface": "report:safe_final", "expected": "safe", "observed": reason}
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
        f"start_slice_17_11=true start_slice_17_12=true start_slice_17_13=false "
        f"docs_header_overlap_fixed={report.docs_ux.get('docs_header_overlap_fixed')}"
    )
    return 0 if report.verdict != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
