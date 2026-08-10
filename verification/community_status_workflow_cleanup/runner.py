"""Slice 17.25 Community Status GitHub authority + workflow cleanup runner."""

from __future__ import annotations

from pathlib import Path

from verification.community_status_workflow_cleanup import PACKAGE_ID, VERSION
from verification.community_status_workflow_cleanup.checks import (
    check_docs,
    check_github_authority,
    check_operational,
    check_policy_and_registers,
    check_prior_slices_and_boundary,
    check_status_live,
    check_website,
    check_workflow_inventory,
    check_workflow_security,
)
from verification.community_status_workflow_cleanup.contract import (
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SOFT_LIMITATION_CODES,
    SUITE_ID,
    SV1725_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_status_workflow_cleanup.determinism import assert_deterministic_payload
from verification.community_status_workflow_cleanup.helpers import dict_to_canonical_json, report_text_is_safe
from verification.community_status_workflow_cleanup.models import CheckResult, Defect, Report, Verdict
from verification.community_status_workflow_cleanup.scenarios import check_scenarios

SOFT_CHECK_IDS = frozenset(
    {
        "status:live",
        "website:site_js",
        "operational:worktree_uncommitted",
        "scenario:X",
    }
)


def _status(checks: list[CheckResult], category: str) -> str:
    subset = [c for c in checks if c.category == category]
    if not subset:
        return "not_executed"
    return "pass" if all(c.ok or c.check_id in SOFT_CHECK_IDS for c in subset) else "fail"


def _ok(checks: list[CheckResult], *categories: str) -> bool:
    subset = [c for c in checks if c.category in categories]
    if not subset:
        return True
    return all(c.ok or c.check_id in SOFT_CHECK_IDS for c in subset)


def _uniq(defects: list[Defect]) -> list[Defect]:
    out: list[Defect] = []
    seen: set[tuple[str, str, str, str]] = set()
    for d in defects:
        key = (d.classification, d.check_id, d.expected, d.detail)
        if key not in seen:
            seen.add(key)
            out.append(d)
    return out


def _decide(
    defects: list[Defect],
    limitations: list[str],
    checks: list[CheckResult],
    *,
    start_slice_17_26: bool,
) -> Verdict:
    if start_slice_17_26:
        return "FAIL"
    hard_failed = sum(1 for c in checks if (not c.ok) and c.check_id not in SOFT_CHECK_IDS)
    if hard_failed or defects:
        return "FAIL"
    if limitations:
        return "PASS_WITH_LIMITATIONS" if set(limitations) <= SOFT_LIMITATION_CODES else "FAIL"
    if any(not c.ok for c in checks):
        return "PASS_WITH_LIMITATIONS"
    return "PASS"


def build_report(monorepo: Path) -> Report:
    contract = default_contract()
    assert contract.start_slice_17_25 is True
    assert contract.start_slice_17_26 is False

    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []

    c, d, policy, workflow_register = check_policy_and_registers(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, github_authority = check_github_authority(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, docs = check_docs(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, website, _ = check_website(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, workflow_inventory, wf_lim = check_workflow_inventory(monorepo, workflow_register)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(wf_lim)

    c, d, security = check_workflow_security(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, status_live, live_lim = check_status_live(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(live_lim)

    c, d, prior_slices = check_prior_slices_and_boundary(monorepo, policy)
    checks.extend(c)
    defects.extend(d)

    c, d, op_lim = check_operational(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(op_lim)

    structural_ok = bool(github_authority.get("module")) and bool(github_authority.get("route"))
    live_reachable = bool(status_live.get("reachable"))
    live_schema_ok = bool(status_live.get("schema_ok")) if live_reachable else structural_ok
    live_no_secrets = bool(status_live.get("no_secrets")) if live_reachable else True
    live_no_version_source = (
        bool(status_live.get("no_version_source")) if live_reachable else bool(github_authority.get("public_no_version_source"))
    )

    scenario_flags = {
        "policy_ok": _ok(checks, "policy"),
        "workflow_register_ok": _ok(checks, "register"),
        "status_register_ok": _ok(checks, "register"),
        "github_cache": bool(github_authority.get("github_cache")),
        "normalize_release_tag": bool(github_authority.get("normalize_release_tag")),
        "resolve_public_engine_version": bool(github_authority.get("resolve_public_engine_version")),
        "public_no_version_source": bool(github_authority.get("public_no_version_source")),
        "no_fabricated_stars": bool(github_authority.get("no_fabricated_stars")),
        "docs_github_release": bool(docs.get("github_release")),
        "website_status_binding": bool(website.get("status_binding")),
        "workflow_inventory": bool(workflow_inventory.get("inventory_ok")),
        "export_guards": _ok(checks, "workflows"),
        "no_root_deploy": all(
            entry.get("absent") is True
            for entry in (workflow_inventory.get("absent_deploy_workflows") or [])
        ),
        "ci_no_deploy": _ok(checks, "workflows"),
        "workflow_secrets_clean": bool(security.get("clean")),
        "live_schema_ok": live_schema_ok,
        "live_no_secrets": live_no_secrets,
        "prior_17_24": prior_slices.get("slice_17_24") is True,
        "start_17_25": policy.get("start_slice_17_25") is True,
        "no_17_26_flag": policy.get("start_slice_17_26") is not True,
        "no_17_26_pkg": not prior_slices.get("slice_17_26_started", False),
        "no_marketplace": policy.get("marketplace_publish") is False,
        "website_no_token": bool(website.get("no_github_token", True)),
        "live_ok_or_soft": live_reachable or structural_ok,
        "no_17_26": (
            policy.get("start_slice_17_26") is not True
            and not prior_slices.get("slice_17_26_started", False)
        ),
        "deterministic": True,
    }
    c, d, scenario_results = check_scenarios(flags=scenario_flags)
    checks.extend(c)
    defects.extend(d)

    defects = _uniq(defects)
    limitations = sorted({x for x in limitations if x in SOFT_LIMITATION_CODES})
    failed = sum(1 for c in checks if (not c.ok) and c.check_id not in SOFT_CHECK_IDS)
    verdict = _decide(
        defects,
        limitations,
        checks,
        start_slice_17_26=policy.get("start_slice_17_26") is True,
    )
    categories = sorted({c.category for c in checks})
    statuses = {cat: _status(checks, cat) for cat in categories}

    report = Report(
        schema=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        package_id=PACKAGE_ID,
        package_version=VERSION,
        epic=17,
        slice="17.25",
        suite_id=SUITE_ID,
        verdict=verdict,
        total_checks=len(checks),
        failed_checks=failed,
        checks=[c.to_dict() for c in checks],
        defects=[d.to_dict() for d in defects],
        limitations=limitations,
        statuses=statuses,
        policy={
            "schema": policy.get("schema"),
            "start_slice_17_25": policy.get("start_slice_17_25"),
            "start_slice_17_26": policy.get("start_slice_17_26"),
            "github_repository": policy.get("github_repository"),
            "github_lookup_ttl_seconds": policy.get("github_lookup_ttl_seconds"),
            "package_version_not_public_sot": policy.get("package_version_not_public_sot"),
        },
        workflow_register={
            "schema": workflow_register.get("schema"),
            "platform_repo_deployment_authority": workflow_register.get(
                "platform_repo_deployment_authority"
            ),
            "workflow_count": len(workflow_register.get("workflows") or []),
        },
        github_authority=github_authority,
        workflow_inventory=workflow_inventory,
        website=website,
        docs=docs,
        status_live={
            "reachable": status_live.get("reachable"),
            "http_status": status_live.get("http_status"),
            "schema_ok": status_live.get("schema_ok"),
            "live_engine_version": status_live.get("live_engine_version"),
            "package_candidate_version": status_live.get("package_candidate_version"),
            "github_shape_ok": status_live.get("github_shape_ok"),
            "no_secrets": status_live.get("no_secrets"),
            "no_version_source": live_no_version_source,
        },
        security=security,
        prior_slices=prior_slices,
        epic17_boundary={"start_slice_17_25": True, "start_slice_17_26": False},
        scenario_results=scenario_results,
    )

    text = dict_to_canonical_json(report.to_dict())
    if not report_text_is_safe(text) or "timestamp" in text or "/Users/" in text:
        report.verdict = "FAIL"
        report.failed_checks = report.failed_checks + 1
        report.checks = list(report.checks) + [
            {
                "check_id": "report:safe_final",
                "ok": False,
                "detail": "unsafe",
                "category": "determinism",
            }
        ]
        report.defects = list(report.defects) + [
            {
                "classification": "report_leak",
                "check_id": "report:safe_final",
                "expected": "safe",
                "detail": "unsafe",
            }
        ]
        report.total_checks = len(report.checks)
        report.scenario_results = {**report.scenario_results, "Z": False}

    return report


def write_report(monorepo: Path, report: Report) -> Path:
    out = monorepo / SV1725_OUTPUT_RELATIVE
    out.mkdir(parents=True, exist_ok=True)
    path = out / REPORT_JSON
    payload = report.to_dict()
    assert_deterministic_payload(payload)
    text = dict_to_canonical_json(payload)
    assert "timestamp" not in text
    assert "/Users/" not in text
    path.write_text(text, encoding="utf-8")
    (out / REPORT_MD).write_text(
        f"# {SCHEMA_NAME}:{SCHEMA_VERSION}\n\n"
        f"Verdict: **{report.verdict}**\n\n"
        f"Checks: {report.total_checks} (failed: {report.failed_checks})\n\n"
        "Slice 17.25 — Community Status GitHub release authority, workflow authority "
        "hygiene, and export-source repository guards. Public engine_version follows "
        "published GitHub Release with package candidate fallback (verification-only "
        "mismatch classification). Slice 17.26 not started.\n",
        encoding="utf-8",
    )
    return path


def main() -> int:
    monorepo = monorepo_root_from_here()
    report = build_report(monorepo)
    path = write_report(monorepo, report)
    print(
        f"{report.verdict} checks={report.total_checks} failed={report.failed_checks} "
        f"report={path.relative_to(monorepo)}"
    )
    print(
        "start_slice_17_25=true start_slice_17_26=false "
        f"status_live={report.status_live.get('reachable')} "
        f"limitations={len(report.limitations)}"
    )
    return 0 if report.verdict != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
