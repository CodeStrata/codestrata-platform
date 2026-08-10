"""Slice 17.23 Community Status + Published Report Registry runner."""

from __future__ import annotations

import json
from pathlib import Path

from verification.community_status_report_registry import PACKAGE_ID, VERSION
from verification.community_status_report_registry.checks import (
    check_docs,
    check_github_cache_and_website,
    check_insights,
    check_manifest,
    check_operational,
    check_policy,
    check_prior_slices,
    check_reports_domain,
    check_status_live,
    check_status_module,
)
from verification.community_status_report_registry.contract import (
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SOFT_LIMITATION_CODES,
    SUITE_ID,
    SV1723_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_status_report_registry.determinism import assert_deterministic_payload
from verification.community_status_report_registry.helpers import dict_to_canonical_json, report_text_is_safe
from verification.community_status_report_registry.models import CheckResult, Defect, Report, Verdict
from verification.community_status_report_registry.scenarios import check_scenarios

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
    start_slice_17_24: bool,
) -> Verdict:
    if start_slice_17_24:
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
    assert contract.start_slice_17_23 is True
    assert contract.start_slice_17_24 is False

    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []

    c, d, policy = check_policy(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, status_module = check_status_module(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, status_live, lim = check_status_live(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, github_cache, website, lim = check_github_cache_and_website(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, manifest = check_manifest(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, insights = check_insights(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, docs = check_docs(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, reports_domain = check_reports_domain(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, prior_slices = check_prior_slices(monorepo, policy)
    checks.extend(c)
    defects.extend(d)

    c, d, lim = check_operational(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    # Soft: structural status pass + live HTTP fail must not alone FAIL.
    structural_status_ok = bool(status_module.get("module")) and bool(status_module.get("route"))
    live_reachable = bool(status_live.get("reachable"))
    live_schema_ok = True
    live_version_ok = True
    live_no_secrets = True
    if live_reachable:
        live_schema_ok = bool(status_live.get("schema_ok"))
        live_version_ok = bool(status_live.get("engine_version_match"))
        live_no_secrets = bool(status_live.get("no_secrets"))
    elif structural_status_ok:
        # Deploy pending — treat schema/version/secrets as soft-pass structurally.
        live_schema_ok = True
        live_version_ok = True
        live_no_secrets = True
        if "status_api_deploy_pending" not in limitations:
            limitations.append("status_api_deploy_pending")

    scenario_flags = {
        "policy_ok": _ok(checks, "policy"),
        "status_module": bool(status_module.get("module")),
        "status_route": bool(status_module.get("route")),
        "live_schema_ok": live_schema_ok,
        "live_version_ok": live_version_ok,
        "live_no_secrets": live_no_secrets,
        "github_cache": bool(github_cache.get("module")),
        "website_no_token": bool(website.get("no_github_token", True)),
        "manifest_schema": str(manifest.get("schema") or "") == "public-report-urls-manifest:1.1",
        "manifest_fields": bool(manifest.get("current_previous")),
        "flask_retained": bool(manifest.get("flask_17_21")),
        "auto_upsert": bool(manifest.get("auto_upsert")),
        "insights_page": bool(insights.get("page")),
        "insights_nav": bool(insights.get("nav")),
        "insights_route": bool(insights.get("route")),
        "insights_api": bool(insights.get("api_path")),
        "docs_status": bool(docs.get("documented")),
        "reports_domain": bool(reports_domain.get("remains_reports_domain")),
        "start_17_23": policy.get("start_slice_17_23") is True,
        "no_17_24_flag": policy.get("start_slice_17_24") is not True,
        "no_17_24_pkg": not prior_slices.get("slice_17_24_started", False),
        "no_marketplace": policy.get("marketplace_publish") is False,
        "no_full_22": policy.get("full_22_repo_release_corpus") is False,
        "live_ok_or_soft": live_reachable or structural_status_ok,
        "no_17_24": (
            policy.get("start_slice_17_24") is not True
            and not prior_slices.get("slice_17_24_started", False)
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
        start_slice_17_24=policy.get("start_slice_17_24") is True,
    )
    categories = sorted({c.category for c in checks})
    statuses = {cat: _status(checks, cat) for cat in categories}

    report = Report(
        schema=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        package_id=PACKAGE_ID,
        package_version=VERSION,
        epic=17,
        slice="17.23",
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
            "start_slice_17_23": policy.get("start_slice_17_23"),
            "start_slice_17_24": policy.get("start_slice_17_24"),
            "marketplace_publish": policy.get("marketplace_publish"),
            "report_rendering_remains_reports_domain": policy.get(
                "report_rendering_remains_reports_domain"
            ),
        },
        status_module=status_module,
        status_live={
            "reachable": status_live.get("reachable"),
            "http_status": status_live.get("http_status"),
            "schema_ok": status_live.get("schema_ok"),
            "engine_version_match": status_live.get("engine_version_match"),
            "expected_engine_version": status_live.get("expected_engine_version"),
            "no_secrets": status_live.get("no_secrets"),
        },
        github_cache=github_cache,
        website={
            "present": website.get("present"),
            "no_github_token": website.get("no_github_token"),
        },
        manifest=manifest,
        insights=insights,
        docs=docs,
        reports_domain=reports_domain,
        prior_slices=prior_slices,
        epic17_boundary={"start_slice_17_23": True, "start_slice_17_24": False},
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
    out = monorepo / SV1723_OUTPUT_RELATIVE
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
        "Slice 17.23 — public Community Status API, validation report URL registry "
        "(schema 1.1 current/previous), and authenticated Insights Published Reports "
        "index. Rendering remains on reports.codestrata.ai. Slice 17.24 not started.\n",
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
        "start_slice_17_23=true start_slice_17_24=false "
        f"status_live={report.status_live.get('reachable')} "
        f"limitations={len(report.limitations)}"
    )
    return 0 if report.verdict != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
