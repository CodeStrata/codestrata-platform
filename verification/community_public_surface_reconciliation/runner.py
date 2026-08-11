"""Slice 18.6 Public Surface Reconciliation runner."""

from __future__ import annotations

from pathlib import Path

from verification.community_public_surface_reconciliation import PACKAGE_ID, VERSION
from verification.community_public_surface_reconciliation.checks import (
    check_boundary,
    check_claims,
    check_cli_surfaces,
    check_contradictions,
    check_docs_and_vscode,
    check_policy,
    check_readme_security_privacy,
    check_stale_strings,
    check_terminology,
    check_version_truth,
)
from verification.community_public_surface_reconciliation.contract import (
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SOFT_LIMITATION_CODES,
    SUITE_ID,
    SV186_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_public_surface_reconciliation.determinism import (
    assert_deterministic_payload,
)
from verification.community_public_surface_reconciliation.helpers import (
    dict_to_canonical_json,
    report_text_is_safe,
)
from verification.community_public_surface_reconciliation.models import (
    CheckResult,
    Defect,
    Report,
    Verdict,
)


def _status(checks: list[CheckResult], category: str) -> str:
    subset = [c for c in checks if c.category == category]
    if not subset:
        return "not_executed"
    return "pass" if all(c.ok for c in subset) else "fail"


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
    start_slice_18_7: bool,
) -> Verdict:
    if start_slice_18_7:
        return "FAIL"
    hard_failed = sum(1 for c in checks if not c.ok)
    if hard_failed or defects:
        return "FAIL"
    if limitations:
        return "PASS_WITH_LIMITATIONS" if set(limitations) <= SOFT_LIMITATION_CODES else "FAIL"
    return "PASS"


def build_report(monorepo: Path) -> Report:
    contract = default_contract()
    assert contract.start_slice_18_6 is True
    assert contract.start_slice_18_7 is False

    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []

    c, d, policy = check_policy(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, lim = check_version_truth(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, texts = check_cli_surfaces(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d = check_readme_security_privacy(texts)
    checks.extend(c)
    defects.extend(d)

    c, d, lim = check_docs_and_vscode(texts)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d = check_terminology(monorepo, texts)
    checks.extend(c)
    defects.extend(d)

    c, d = check_stale_strings(texts)
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

    defects = _uniq(defects)
    limitations = sorted({x for x in limitations if x in SOFT_LIMITATION_CODES})
    failed = sum(1 for c in checks if not c.ok)
    verdict = _decide(
        defects,
        limitations,
        checks,
        start_slice_18_7=policy.get("start_slice_18_7") is True,
    )
    categories = sorted({c.category for c in checks})
    statuses = {cat: _status(checks, cat) for cat in categories}

    report = Report(
        schema=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        package_id=PACKAGE_ID,
        package_version=VERSION,
        epic=18,
        slice="18.6",
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
            "start_slice_18_6": policy.get("start_slice_18_6"),
            "start_slice_18_7": policy.get("start_slice_18_7"),
            "bare_cli_truthful": policy.get("bare_cli_truthful"),
            "installed_version_truthful": policy.get("installed_version_truthful"),
        },
        coverage={"claims": len(claims)},
        claims=claims,
        epic18_boundary={"start_slice_18_6": True, "start_slice_18_7": False},
        freeze_confirmations={
            "no_product_capability_redesign": True,
            "no_telemetry_schema_change": True,
            "no_community_api_redesign": True,
            "no_cli_publish": True,
            "no_vscode_marketplace_publish": True,
            "no_release_tag": True,
            "no_full_22_repository_release_corpus": True,
            "slice_18_7_not_started": True,
        },
        docs_deployment={
            "canonical_docs_base": "https://docs.codestrata.ai",
            "live_verification": "operator_curl",
        },
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
    out = monorepo / SV186_OUTPUT_RELATIVE
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
        "Slice 18.6 — Public Surface Reconciliation. "
        "No product redesign. Slice 18.7 not started.\n",
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
        "start_slice_18_6=true start_slice_18_7=false "
        f"limitations={len(report.limitations)}"
    )
    return 0 if report.verdict != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
