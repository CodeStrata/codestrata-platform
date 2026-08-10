"""Slice 17.27 Epic 17 completion verification runner."""

from __future__ import annotations

from pathlib import Path

from verification.community_epic17_completion import PACKAGE_ID, VERSION
from verification.community_epic17_completion.checks import (
    check_ai_providers,
    check_assessment_eir,
    check_capability_matrix,
    check_community_status,
    check_data_lake_insights_source,
    check_defects_and_carry_forwards,
    check_docs_branding,
    check_exports,
    check_insights_auth,
    check_policy,
    check_prior_suites,
    check_production_health,
    check_security,
    check_telemetry_and_publish,
    check_vscode,
    check_workflows,
    check_worktree,
    check_zero_drift,
    write_transparency_handoff,
)
from verification.community_epic17_completion.contract import (
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SOFT_LIMITATION_CODES,
    SUITE_ID,
    SV1727_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_epic17_completion.determinism import (
    assert_deterministic_payload,
)
from verification.community_epic17_completion.helpers import (
    dict_to_canonical_json,
    report_text_is_safe,
)
from verification.community_epic17_completion.models import (
    CheckResult,
    Defect,
    EpicVerdict,
    Report,
    Verdict,
)

SOFT_CHECK_IDS = frozenset(
    {
        "status:release_gap_expected",
        "branding:codestrata_ai_favicon",
        "insights_auth:browser_ux_not_hiding_api_success",
        "assessment:current_html_evidence",
        "telemetry:default_off_source",
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


def _decide_suite(
    defects: list[Defect],
    limitations: list[str],
    checks: list[CheckResult],
    *,
    transparency_started: bool,
    release_started: bool,
) -> Verdict:
    if transparency_started or release_started:
        return "FAIL"
    hard_failed = sum(1 for c in checks if (not c.ok) and c.check_id not in SOFT_CHECK_IDS)
    if hard_failed or defects:
        return "FAIL"
    if limitations:
        return "PASS_WITH_LIMITATIONS" if set(limitations) <= SOFT_LIMITATION_CODES else "FAIL"
    if any(not c.ok for c in checks):
        return "PASS_WITH_LIMITATIONS"
    return "PASS"


def _decide_epic(
    *,
    suite_verdict: Verdict,
    defects: list[Defect],
    checks: list[CheckResult],
    carry: list[dict],
    zero_drift: dict,
    capability: dict[str, str],
) -> EpicVerdict:
    blockers = [k for k, v in capability.items() if v == "BLOCKER"]
    hard = [c for c in checks if (not c.ok) and c.check_id not in SOFT_CHECK_IDS]
    if blockers or hard or defects or suite_verdict == "FAIL":
        return "EPIC_BLOCKED"
    if zero_drift.get("zero_drift") is not True:
        return "EPIC_BLOCKED"
    if carry:
        return "EPIC_COMPLETE_WITH_RELEASE_CARRY_FORWARDS"
    return "EPIC_COMPLETE"


def build_report(monorepo: Path) -> Report:
    contract = default_contract()
    assert contract.start_slice_17_27 is True
    assert contract.start_transparency_documentation_epic is False
    assert contract.start_release_readiness_epic is False

    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []

    c, d, policy = check_policy(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, _prior = check_prior_suites(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, capability = check_capability_matrix(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, health = check_production_health(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, auth = check_insights_auth(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, status, lim = check_community_status(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, _tel = check_telemetry_and_publish(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, _lake = check_data_lake_insights_source(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, _assess = check_assessment_eir(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, _ai, lim = check_ai_providers(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, _vscode, lim = check_vscode(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, branding, lim = check_docs_branding(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, _wf = check_workflows(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, zero_drift = check_zero_drift(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, security = check_security(monorepo)
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

    c, d, defect_entries, carry, lim = check_defects_and_carry_forwards(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    transparency = write_transparency_handoff(monorepo)

    defects = _uniq(defects)
    limitations = sorted({x for x in limitations if x in SOFT_LIMITATION_CODES})
    failed = sum(1 for c in checks if (not c.ok) and c.check_id not in SOFT_CHECK_IDS)
    suite_verdict = _decide_suite(
        defects,
        limitations,
        checks,
        transparency_started=policy.get("start_transparency_documentation_epic") is True,
        release_started=policy.get("start_release_readiness_epic") is True,
    )
    epic_verdict = _decide_epic(
        suite_verdict=suite_verdict,
        defects=defects,
        checks=checks,
        carry=carry,
        zero_drift=zero_drift,
        capability=capability,
    )
    categories = sorted({c.category for c in checks})
    statuses = {cat: _status(checks, cat) for cat in categories}

    report = Report(
        schema=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        package_id=PACKAGE_ID,
        package_version=VERSION,
        epic=17,
        slice="17.27",
        suite_id=SUITE_ID,
        verdict=suite_verdict,
        epic_verdict=epic_verdict,
        total_checks=len(checks),
        failed_checks=failed,
        checks=[c.to_dict() for c in checks],
        defects=[d.to_dict() for d in defects],
        limitations=limitations,
        statuses=statuses,
        policy={
            "schema": policy.get("schema"),
            "slice": policy.get("slice"),
            "epic17_feature_work_complete": policy.get("epic17_feature_work_complete"),
            "production_zero_drift": policy.get("production_zero_drift"),
            "start_slice_17_27": policy.get("start_slice_17_27"),
            "start_transparency_documentation_epic": policy.get(
                "start_transparency_documentation_epic"
            ),
            "start_release_readiness_epic": policy.get("start_release_readiness_epic"),
            "no_cli_publish": policy.get("no_cli_publish"),
            "no_vscode_marketplace_publish": policy.get("no_vscode_marketplace_publish"),
            "no_release_tag": policy.get("no_release_tag"),
            "no_release_commit": policy.get("no_release_commit"),
            "no_full_22_repository_release_corpus": policy.get(
                "no_full_22_repository_release_corpus"
            ),
        },
        capability_matrix=capability,
        production_health=health,
        insights_auth={
            "wrong_code": (auth.get("wrong") or {}).get("code"),
            "correct": (auth.get("correct") or {}).get("http_status"),
            "overview": (auth.get("overview") or {}).get("http_status"),
            "logout": (auth.get("logout") or {}).get("http_status"),
            "post_logout_overview": (auth.get("post_logout_overview") or {}).get(
                "http_status"
            ),
            "browser_ux": (auth.get("browser_ux") or {}).get("classification"),
        },
        community_status={
            "github_repository": status.get("github_repository"),
            "engine_version": status.get("engine_version"),
            "github_stars_source": status.get("github_stars_source"),
        },
        zero_drift={
            "add": zero_drift.get("add"),
            "change": zero_drift.get("change"),
            "destroy": zero_drift.get("destroy"),
            "zero_drift": zero_drift.get("zero_drift"),
            "apply_performed": zero_drift.get("apply_performed"),
        },
        defect_inventory=[
            {
                "defect_id": e.get("defect_id"),
                "current_status": e.get("current_status"),
                "release_disposition": e.get("release_disposition"),
            }
            for e in defect_entries
        ],
        release_carry_forwards=[
            {"item_id": e.get("item_id"), "description": e.get("description")}
            for e in carry
        ],
        transparency_handoff={
            "started": False,
            "topic_count": len(transparency.get("topics") or []),
        },
        worktree=worktree,
        security_scan={
            "clean": security.get("clean"),
            "files_scanned": security.get("files_scanned"),
            "secret_hits": security.get("secret_hits"),
        },
        export_readiness={
            "community": ((exports.get("targets") or {}).get("community") or {}).get(
                "status"
            ),
            "insights": ((exports.get("targets") or {}).get("insights") or {}).get(
                "status"
            ),
            "infrastructure": ((exports.get("targets") or {}).get("infrastructure") or {}).get(
                "status"
            ),
            "push_performed": exports.get("push_performed"),
        },
        epic17_boundary={
            "start_slice_17_27": True,
            "start_transparency_documentation_epic": False,
            "start_release_readiness_epic": False,
        },
        freeze_confirmations={
            "epic17_feature_implementation_frozen": True,
            "no_release_commit": True,
            "no_release_tag": True,
            "no_cli_publish": True,
            "no_vscode_marketplace_publish": True,
            "no_full_22_repository_release_corpus": True,
        },
    )

    text = dict_to_canonical_json(report.to_dict())
    if not report_text_is_safe(text) or "timestamp" in text or "/Users/" in text:
        report.verdict = "FAIL"
        report.epic_verdict = "EPIC_BLOCKED"
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

    return report


def write_report(monorepo: Path, report: Report) -> Path:
    out = monorepo / SV1727_OUTPUT_RELATIVE
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
        f"Suite verdict: **{report.verdict}**\n\n"
        f"Epic verdict: **{report.epic_verdict}**\n\n"
        f"Checks: {report.total_checks} (failed: {report.failed_checks})\n\n"
        "Slice 17.27 — Epic 17 Completion Verification. Feature implementation frozen. "
        "No Transparency Documentation Epic. No Release Readiness Epic. "
        "No release commit/tag/CLI/Marketplace publish. No full 22-repo corpus.\n",
        encoding="utf-8",
    )
    return path


def main() -> int:
    monorepo = monorepo_root_from_here()
    report = build_report(monorepo)
    path = write_report(monorepo, report)
    print(
        f"{report.verdict} epic={report.epic_verdict} "
        f"checks={report.total_checks} failed={report.failed_checks} "
        f"report={path.relative_to(monorepo)}"
    )
    print(
        "start_slice_17_27=true transparency=false release=false "
        f"limitations={len(report.limitations)} carry_forwards={len(report.release_carry_forwards)}"
    )
    return 0 if report.verdict != "FAIL" and report.epic_verdict != "EPIC_BLOCKED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
