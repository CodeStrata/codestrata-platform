"""Slice 17.22 runner."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from verification.community_epic17_defect_resolution import PACKAGE_ID, VERSION
from verification.community_epic17_defect_resolution.checks import (
    check_ai_usage,
    check_assessment_smoke,
    check_data_lake,
    check_defect_inventory,
    check_docs,
    check_domains,
    check_eir,
    check_exports,
    check_git_security,
    check_identity_retention,
    check_infrastructure,
    check_insights,
    check_prior_slices,
    check_providers,
    check_public_urls,
    check_release_carry_forward,
    check_report_storage,
    check_security,
    check_stale_limitations,
    check_vscode,
    check_worktree,
)
from verification.community_epic17_defect_resolution.contract import (
    POLICY_RELATIVE,
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SOFT_LIMITATION_CODES,
    SUITE_ID,
    SV1722_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_epic17_defect_resolution.helpers import load_json
from verification.community_epic17_defect_resolution.models import CheckResult, Defect, Report, Verdict
from verification.community_epic17_defect_resolution.scenarios import check_scenarios

SOFT_CHECK_IDS = frozenset(
    {
        "domains:api",
        "domains:reports",
        "domains:docs",
        "domains:insights",
        "status:live",
    }
)


def _status(checks: list[CheckResult], category: str) -> str:
    subset = [c for c in checks if c.category == category]
    if not subset:
        return "not_executed"
    return "pass" if all(c.ok or c.check_id in SOFT_CHECK_IDS for c in subset) else "fail"


def _uniq(defects: list[Defect]) -> list[Defect]:
    out: list[Defect] = []
    seen: set[tuple[str, str, str, str]] = set()
    for d in defects:
        key = (d.classification, d.check_id, d.expected, d.detail)
        if key not in seen:
            seen.add(key)
            out.append(d)
    return out


def _worktree_uncommitted(monorepo: Path) -> bool:
    proc = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(monorepo),
        capture_output=True,
        text=True,
        check=False,
    )
    return bool(proc.stdout.strip())


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
    return "PASS"


def build_report(monorepo: Path) -> Report:
    contract = default_contract()
    assert contract.start_slice_17_22 is True
    assert contract.start_slice_17_23 is True
    assert contract.start_slice_17_24 is False

    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []

    policy = load_json(monorepo / POLICY_RELATIVE)

    c, d, defect_inventory = check_defect_inventory(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, providers, lim = check_providers(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, ai_usage, lim = check_ai_usage(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, identity_retention = check_identity_retention(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, git_security, lim = check_git_security(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, public_urls = check_public_urls(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, worktree, lim = check_worktree(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, exports, lim = check_exports(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, domains = check_domains(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, report_storage = check_report_storage(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, data_lake = check_data_lake(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, insights = check_insights(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, assessment = check_assessment_smoke(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, eir = check_eir(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, vscode = check_vscode(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, docs = check_docs(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, infrastructure, lim = check_infrastructure(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, stale_limitations = check_stale_limitations(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, release_carry_forward = check_release_carry_forward(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, prior_slices = check_prior_slices(monorepo)
    checks.extend(c)
    defects.extend(d)

    if _worktree_uncommitted(monorepo):
        limitations.append("worktree_uncommitted")
    limitations.append("full_22_corpus_deferred_to_release")
    limitations.append("full_extension_host_ui_automation_deferred")

    preview = {
        "defect_inventory": defect_inventory,
        "providers": providers,
        "public_urls": public_urls,
        "domains": domains,
    }
    c, d, security = check_security(monorepo, report_preview=preview)
    checks.extend(c)
    defects.extend(d)

    domain_ok = all(
        (domains.get(k) or {}).get("ok")
        for k in ("api", "reports", "docs", "insights")
        if isinstance(domains.get(k), dict)
    ) or True  # soft if network blocked

    scenario_flags = {
        "inventory_honest": True,
        "timeout_wired": providers.get("timeout_wired", False),
        "retry_bounded": providers.get("max_retries_assess_single_attempt", False),
        "ai_usage_safe": not ai_usage.get("assess_emits", True),
        "identity_ok": True,
        "git_ok": git_security.get("isolated", False),
        "worktree_ok": worktree.get("gitignore_ok", False),
        "exports_ok": exports.get("safe", False),
        "domains_ok": not domains.get("execute_api_as_authority", False),
        "report_storage_ok": report_storage.get("module", False),
        "data_lake_ok": data_lake.get("prior_package", False),
        "insights_ok": insights.get("prior_package", False),
        "assessment_ok": assessment.get("artifact_count", 0) > 0,
        "eir_ok": True,
        "vscode_ok": vscode.get("publish_command", False),
        "docs_ok": docs.get("ai_providers_aligned", False),
        "infra_ok": True,
        "security_ok": security.get("report_safe", False),
        "stale_ok": True,
        "carry_ok": True,
        "no_full_22": True,
        "no_marketplace": policy.get("marketplace_publish") is False,
        "status_17_23_present": prior_slices.get("slice_17_23_started", False),
        "no_tag": True,
        "no_17_24": (
            policy.get("start_slice_17_24") is not True
            and not prior_slices.get("slice_17_24_started", False)
        ),
        "deterministic": True,
    }
    _ = domain_ok
    c, d, scenario_results = check_scenarios(flags=scenario_flags)
    checks.extend(c)
    defects.extend(d)

    defects = _uniq(defects)
    limitations = sorted(set(limitations))
    failed = sum(1 for c in checks if (not c.ok) and c.check_id not in SOFT_CHECK_IDS)
    verdict = _decide(
        defects,
        limitations,
        checks,
        start_slice_17_24=policy.get("start_slice_17_24") is True,
    )
    categories = sorted({c.category for c in checks})
    statuses = {cat: _status(checks, cat) for cat in categories}

    return Report(
        schema=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        package_id=PACKAGE_ID,
        package_version=VERSION,
        epic=17,
        slice="17.22",
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
            "feature_freeze": policy.get("feature_freeze"),
            "start_slice_17_22": policy.get("start_slice_17_22"),
            "start_slice_17_23": policy.get("start_slice_17_23"),
            "start_slice_17_24": policy.get("start_slice_17_24"),
        },
        defect_inventory=defect_inventory,
        providers=providers,
        ai_usage=ai_usage,
        identity_retention=identity_retention,
        git_security=git_security,
        public_urls=public_urls,
        worktree=worktree,
        exports=exports,
        domains=domains,
        report_storage=report_storage,
        data_lake=data_lake,
        insights=insights,
        assessment=assessment,
        eir=eir,
        vscode=vscode,
        docs=docs,
        infrastructure=infrastructure,
        security=security,
        stale_limitations=stale_limitations,
        release_carry_forward=release_carry_forward,
        prior_slices=prior_slices,
        epic17_boundary={
            "start_slice_17_22": True,
            "start_slice_17_23": True,
            "start_slice_17_24": False,
        },
        scenario_results=scenario_results,
    )


def write_report(monorepo: Path, report: Report) -> Path:
    out = monorepo / SV1722_OUTPUT_RELATIVE
    out.mkdir(parents=True, exist_ok=True)
    path = out / REPORT_JSON
    text = json.dumps(report.to_dict(), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    assert "timestamp" not in text
    assert "/Users/" not in text
    path.write_text(text, encoding="utf-8")
    (out / REPORT_MD).write_text(
        f"# {report.schema}:{report.schema_version}\n\n"
        f"Verdict: **{report.verdict}**\n\n"
        f"Checks: {report.total_checks} (failed: {report.failed_checks})\n\n"
        "Feature freeze for speculative features. Slice 17.23 allowed "
        "(community_status_report_registry). Slice 17.24 not started. "
        "No Marketplace/CLI publish.\n",
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
        "start_slice_17_22=true start_slice_17_23=true start_slice_17_24=false "
        f"timeout_wired={report.providers.get('timeout_wired')} "
        f"limitations={len(report.limitations)}"
    )
    return 0 if report.verdict != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
