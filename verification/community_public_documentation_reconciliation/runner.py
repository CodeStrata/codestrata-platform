"""Slice 17.26 Community public documentation reconciliation runner."""

from __future__ import annotations

from pathlib import Path

from verification.community_public_documentation_reconciliation import PACKAGE_ID, VERSION
from verification.community_public_documentation_reconciliation.checks import (
    check_gitignore,
    check_live_soft,
    check_policy,
    check_privacy_docs,
    check_reports_landing,
    check_stale_report_paths,
)
from verification.community_public_documentation_reconciliation.contract import (
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SOFT_LIMITATION_CODES,
    SUITE_ID,
    SV1726_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_public_documentation_reconciliation.determinism import (
    assert_deterministic_payload,
)
from verification.community_public_documentation_reconciliation.helpers import (
    dict_to_canonical_json,
    report_text_is_safe,
)
from verification.community_public_documentation_reconciliation.models import (
    CheckResult,
    Defect,
    Report,
    Verdict,
)

SOFT_CHECK_IDS = frozenset(
    {
        "live:docs_privacy",
        "live:reports_favicon",
        "live:reports_landing_privacy",
        "live:corporate_favicon_identity",
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


def _decide(
    defects: list[Defect],
    limitations: list[str],
    checks: list[CheckResult],
    *,
    start_slice_17_27: bool,
) -> Verdict:
    if start_slice_17_27:
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
    assert contract.start_slice_17_26 is True
    assert contract.start_slice_17_27 is False

    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []

    c, d, policy = check_policy(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, privacy_docs = check_privacy_docs(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, stale = check_stale_report_paths(monorepo)
    checks.extend(c)
    defects.extend(d)
    privacy_docs = {**privacy_docs, "stale_report_paths": stale}

    c, d, reports_landing = check_reports_landing(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, gitignore = check_gitignore(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, live, live_lim = check_live_soft(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(live_lim)

    defects = _uniq(defects)
    limitations = sorted({x for x in limitations if x in SOFT_LIMITATION_CODES})
    failed = sum(1 for c in checks if (not c.ok) and c.check_id not in SOFT_CHECK_IDS)
    verdict = _decide(
        defects,
        limitations,
        checks,
        start_slice_17_27=policy.get("start_slice_17_27") is True,
    )
    categories = sorted({c.category for c in checks})
    statuses = {cat: _status(checks, cat) for cat in categories}

    report = Report(
        schema=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        package_id=PACKAGE_ID,
        package_version=VERSION,
        epic=17,
        slice="17.26",
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
            "slice": policy.get("slice"),
            "start_slice_17_26": policy.get("start_slice_17_26"),
            "start_slice_17_27": policy.get("start_slice_17_27"),
            "canonical_community_privacy_url": policy.get("canonical_community_privacy_url"),
            "corporate_privacy_url": policy.get("corporate_privacy_url"),
            "no_cli_publish": policy.get("no_cli_publish"),
            "no_vscode_marketplace_publish": policy.get("no_vscode_marketplace_publish"),
            "no_release_tag": policy.get("no_release_tag"),
            "no_full_22_repository_release_corpus": policy.get(
                "no_full_22_repository_release_corpus"
            ),
        },
        privacy_docs=privacy_docs,
        reports_landing=reports_landing,
        gitignore=gitignore,
        live={
            "docs_privacy": (live.get("docs_privacy") or {}).get("http_status"),
            "reports_favicon": (live.get("reports_favicon") or {}).get("http_status"),
            "reports_landing": (live.get("reports_landing") or {}).get("http_status"),
            "corporate_favicon_stale": (live.get("corporate_home") or {}).get(
                "favicon_stale"
            ),
        },
        epic17_boundary={"start_slice_17_26": True, "start_slice_17_27": False},
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
    out = monorepo / SV1726_OUTPUT_RELATIVE
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
        "Slice 17.26 — Community public documentation reconciliation "
        "(canonical privacy authority, reports landing privacy/favicon, "
        "docs stale-path hygiene, gitignore guards). Slice 17.27 not started.\n",
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
        "start_slice_17_26=true start_slice_17_27=false "
        f"limitations={len(report.limitations)}"
    )
    return 0 if report.verdict != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
