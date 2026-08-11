"""Slice 18.5 Community Cloud Architecture Transparency runner."""

from __future__ import annotations

from pathlib import Path

from verification.community_cloud_architecture_transparency import PACKAGE_ID, VERSION
from verification.community_cloud_architecture_transparency.checks import (
    check_api_authority,
    check_boundary,
    check_claims,
    check_contradictions,
    check_data_lake,
    check_docs_present,
    check_failure_security_diagram,
    check_ingestion_and_producers,
    check_insights,
    check_language,
    check_live_docs,
    check_navigation,
    check_policy,
    check_reports_and_status,
    check_routes,
)
from verification.community_cloud_architecture_transparency.contract import (
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SOFT_LIMITATION_CODES,
    SUITE_ID,
    SV185_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_cloud_architecture_transparency.determinism import (
    assert_deterministic_payload,
)
from verification.community_cloud_architecture_transparency.helpers import (
    dict_to_canonical_json,
    report_text_is_safe,
)
from verification.community_cloud_architecture_transparency.models import (
    CheckResult,
    Defect,
    Report,
    Verdict,
)


def _is_soft(check_id: str) -> bool:
    return check_id.startswith("live:")


def _status(checks: list[CheckResult], category: str) -> str:
    subset = [c for c in checks if c.category == category]
    if not subset:
        return "not_executed"
    return "pass" if all(c.ok or _is_soft(c.check_id) for c in subset) else "fail"


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
    start_slice_18_6: bool,
) -> Verdict:
    if start_slice_18_6:
        return "FAIL"
    hard_failed = sum(1 for c in checks if (not c.ok) and not _is_soft(c.check_id))
    if hard_failed or defects:
        return "FAIL"
    if limitations:
        return "PASS_WITH_LIMITATIONS" if set(limitations) <= SOFT_LIMITATION_CODES else "FAIL"
    if any(not c.ok for c in checks):
        return "PASS_WITH_LIMITATIONS"
    return "PASS"


def build_report(monorepo: Path) -> Report:
    contract = default_contract()
    assert contract.start_slice_18_5 is True
    assert contract.start_slice_18_6 is False

    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []

    c, d, policy = check_policy(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, texts = check_docs_present(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d = check_api_authority(texts)
    checks.extend(c)
    defects.extend(d)

    c, d = check_routes(monorepo, texts)
    checks.extend(c)
    defects.extend(d)

    c, d, lim = check_ingestion_and_producers(texts)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d = check_data_lake(texts)
    checks.extend(c)
    defects.extend(d)

    c, d = check_insights(texts)
    checks.extend(c)
    defects.extend(d)

    c, d = check_reports_and_status(texts)
    checks.extend(c)
    defects.extend(d)

    c, d = check_failure_security_diagram(texts)
    checks.extend(c)
    defects.extend(d)

    c, d = check_language(texts)
    checks.extend(c)
    defects.extend(d)

    c, d = check_navigation(monorepo, texts)
    checks.extend(c)
    defects.extend(d)

    c, d, claims = check_claims(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d = check_contradictions(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, lim = check_boundary(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, lim, live = check_live_docs()
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    defects = _uniq(defects)
    limitations = sorted({x for x in limitations if x in SOFT_LIMITATION_CODES})
    failed = sum(1 for c in checks if (not c.ok) and not _is_soft(c.check_id))
    verdict = _decide(
        defects,
        limitations,
        checks,
        start_slice_18_6=policy.get("start_slice_18_6") is True,
    )
    categories = sorted({c.category for c in checks})
    statuses = {cat: _status(checks, cat) for cat in categories}

    report = Report(
        schema=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        package_id=PACKAGE_ID,
        package_version=VERSION,
        epic=18,
        slice="18.5",
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
            "start_slice_18_5": policy.get("start_slice_18_5"),
            "start_slice_18_6": policy.get("start_slice_18_6"),
            "api_authority_documented": policy.get("api_authority_documented"),
            "report_store_separate_documented": policy.get(
                "report_store_separate_documented"
            ),
        },
        coverage={"claims": len(claims), "routes": 16},
        claims=claims,
        epic18_boundary={"start_slice_18_5": True, "start_slice_18_6": False},
        freeze_confirmations={
            "no_runtime_redesign": True,
            "no_telemetry_schema_changes": True,
            "no_data_lake_redesign": True,
            "no_insights_redesign": True,
            "no_community_api_behavior_change": True,
            "no_cli_publish": True,
            "no_vscode_marketplace_publish": True,
            "no_release_tag": True,
            "no_full_22_repository_release_corpus": True,
            "slice_18_6_not_started": True,
        },
        docs_deployment={"live_http_status": live},
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
    return report


def write_report(monorepo: Path, report: Report) -> Path:
    out = monorepo / SV185_OUTPUT_RELATIVE
    out.mkdir(parents=True, exist_ok=True)
    path = out / REPORT_JSON
    payload = report.to_dict()
    assert_deterministic_payload(payload)
    text = dict_to_canonical_json(payload)
    path.write_text(text, encoding="utf-8")
    (out / REPORT_MD).write_text(
        f"# {SCHEMA_NAME}:{SCHEMA_VERSION}\n\n"
        f"Verdict: **{report.verdict}**\n\n"
        f"Checks: {report.total_checks} (failed: {report.failed_checks})\n\n"
        "Slice 18.5 — Community Cloud Architecture Transparency. "
        "No runtime redesign. Slice 18.6 not started.\n",
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
        "start_slice_18_5=true start_slice_18_6=false "
        f"limitations={len(report.limitations)}"
    )
    return 0 if report.verdict != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
