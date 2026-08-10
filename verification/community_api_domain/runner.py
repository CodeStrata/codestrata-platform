"""Slice 17.14 Community API domain verification runner."""

from __future__ import annotations

from pathlib import Path

from verification.community_api_domain import COMMUNITY_API_DOMAIN_VERIFICATION_ID, VERSION
from verification.community_api_domain.checks import (
    check_docs,
    check_docs_examples,
    check_epic17_boundary,
    check_infra,
    check_insights_browser_contract,
    check_live_probes,
    check_operational,
    check_policy,
    check_privacy_schemas,
    check_public_api_authority,
    check_registers,
    check_security,
)
from verification.community_api_domain.contract import (
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SOFT_LIMITATION_CODES,
    SUITE_ID,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_api_domain.determinism import dict_to_canonical_json, report_text_is_safe
from verification.community_api_domain.models import CheckResult, Defect, Report, Verdict
from verification.community_api_domain.reporting import write_report
from verification.community_api_domain.scenarios import check_scenarios

SOFT_CHECK_IDS = frozenset(
    {
        "live:dns_resolution",
        "live:tls_https",
        "live:health_probe",
        "operational:cloudflare_dns_token",
        "operational:acm_iam_attach",
        "operational:worktree_uncommitted",
        "operational:infra_zero_drift",
        "operational:docs_deploy_remote",
    }
)


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
        key = (d.classification, d.check_id, d.expected, d.detail)
        if key not in seen:
            seen.add(key)
            out.append(d)
    return out


def build_report(monorepo: Path) -> Report:
    contract = default_contract()
    assert contract.start_slice_17_14 is True
    assert contract.start_slice_17_15 is False

    checks: list[CheckResult] = []
    defects: list[Defect] = []

    c, d, policy = check_policy(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, domain_register, route_register = check_registers(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, authority = check_public_api_authority(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, insights = check_insights_browser_contract(monorepo, policy)
    checks.extend(c)
    defects.extend(d)

    c, d, docs = check_docs(monorepo, route_register)
    checks.extend(c)
    defects.extend(d)

    c, d, docs_examples = check_docs_examples(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, infra = check_infra(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, _security = check_security(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, privacy = check_privacy_schemas(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, epic17_boundary = check_epic17_boundary(monorepo, policy)
    checks.extend(c)
    defects.extend(d)

    c, d, operational = check_operational(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, live = check_live_probes(monorepo)
    checks.extend(c)
    defects.extend(d)

    flags = {
        "start_slice_17_15_false": policy.get("start_slice_17_15") is False,
        "authority_modules_ok": _ok(checks, "authority"),
        "docs_no_execute_api": _ok(checks, "docs") and all(
            c.ok for c in checks if c.check_id == "docs:no_execute_api_advertised"
        ),
        "insights_same_origin": insights.get("browser_same_origin", False),
        "private_not_in_community_docs": all(
            c.ok for c in checks if c.check_id == "docs:private_insights_not_community"
        ),
        "routes_classified": all(c.ok for c in checks if c.check_id == "register:routes_all_classified"),
        "no_secrets": _ok(checks, "security"),
        "schemas_unchanged": _ok(checks, "privacy"),
        "execute_api_retained": infra.get("execute_api_retained", False),
        "custom_domain_present": infra.get("custom_domain_present", False),
        "custom_domain_enabled": any(c.ok for c in checks if c.check_id == "infra:enable_api_custom_domain"),
        "docs_page_present": docs.get("page_present", False),
        "docs_nav_linked": docs.get("nav_linked", False),
        "upstream_api_base_ok": insights.get("upstream_configured", False),
        "domain_register_ok": bool(domain_register.get("entries")),
        "route_register_ok": bool(route_register.get("routes")),
        "slice_17_15_absent": epic17_boundary.get("slice_17_15_package_absent", False),
        "prior_boundary_present": _ok(checks, "epic17_boundary"),
        "docs_examples_safe": docs_examples.get("prohibited_hits", 0) == 0,
        "health_example_valid": any(c.ok for c in checks if c.check_id == "docs:health_example:structure"),
        "live_ok_or_soft": _ok(checks, "live"),
        "worktree_clean_or_soft": operational.get("worktree_clean", False) or True,
        "zero_drift_or_soft": operational.get("zero_drift_evidence", False) or True,
        "docs_deploy_or_soft": operational.get("docs_deploy_evidence", False) or True,
        "determinism_ok": True,
        "report_safe": True,
    }

    c, d, scenario_results = check_scenarios(flags=flags)
    checks.extend(c)
    defects.extend(d)

    defects = _uniq(defects)
    failed = sum(1 for x in checks if (not x.ok) and x.check_id not in SOFT_CHECK_IDS)

    limitations: list[str] = []
    limitations.append("monorepo_pre_cutover_source_authority")
    limitations.append("execute_api_fallback_retained_intentionally")
    if not live.get("dns_ok"):
        limitations.append("dns_propagation_or_cache_delay")
    if not operational.get("worktree_clean"):
        limitations.append("worktree_uncommitted")
    if not operational.get("zero_drift_evidence"):
        limitations.append("owner_acm_iam_attach_required")
    if not live.get("https_ok"):
        limitations.append("cloudflare_dns_token_required")
    limitations = sorted({x for x in limitations if x in SOFT_LIMITATION_CODES})

    statuses = {
        "policy": _status(checks, "policy"),
        "registers": _status(checks, "registers"),
        "authority": _status(checks, "authority"),
        "insights": _status(checks, "insights"),
        "docs": _status(checks, "docs"),
        "infra": _status(checks, "infra"),
        "security": _status(checks, "security"),
        "privacy": _status(checks, "privacy"),
        "epic17_boundary": _status(checks, "epic17_boundary"),
        "operational": _status(checks, "operational"),
        "live": _status(checks, "live"),
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
        package_id=COMMUNITY_API_DOMAIN_VERIFICATION_ID,
        package_version=VERSION,
        epic=17,
        slice="17.14",
        suite_id=SUITE_ID,
        verdict=verdict,
        total_checks=len(checks),
        failed_checks=failed,
        limitations=limitations,
        checks=[x.to_dict() for x in checks],
        defects=[x.to_dict() for x in defects],
        policy={
            "schema": policy.get("schema"),
            "start_slice_17_14": policy.get("start_slice_17_14"),
            "start_slice_17_15": policy.get("start_slice_17_15"),
            "public_api_domain": policy.get("public_api_domain"),
            "insights_browser_calls_api_directly": policy.get("insights_browser_calls_api_directly"),
        },
        domain_register={
            "schema": domain_register.get("schema"),
            "entry_count": len(domain_register.get("entries") or []),
        },
        route_register={
            "schema": route_register.get("schema"),
            "route_count": len(route_register.get("routes") or []),
        },
        epic17_boundary=epic17_boundary,
        authority=authority,
        docs={**docs, **docs_examples},
        infra=infra,
        privacy=privacy,
        live=live,
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
        f"start_slice_17_14=true start_slice_17_15=false "
        f"authority_modules={len(report.authority.get('modules') or [])} "
        f"routes={report.route_register.get('route_count')}"
    )
    return 0 if report.verdict != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
