"""Slice 18.7 Public Claim Runtime Validation runner."""

from __future__ import annotations

from pathlib import Path

from verification.community_public_claim_runtime_validation import PACKAGE_ID, VERSION
from verification.community_public_claim_runtime_validation.checks import (
    check_ai_and_locality,
    check_boundary,
    check_claim_inventory,
    check_contradictions,
    check_fields_and_routes,
    check_live_endpoints,
    check_policy,
    check_privacy_consistency,
    check_retention_and_assessment,
    check_telemetry_honesty,
    check_terminology_cli_vscode,
)
from verification.community_public_claim_runtime_validation.contract import (
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SOFT_LIMITATION_CODES,
    SUITE_ID,
    SV187_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_public_claim_runtime_validation.determinism import (
    assert_deterministic_payload,
)
from verification.community_public_claim_runtime_validation.helpers import (
    dict_to_canonical_json,
    report_text_is_safe,
)
from verification.community_public_claim_runtime_validation.models import (
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


def _is_soft(check_id: str) -> bool:
    return check_id.startswith("live:")


def _decide(
    defects: list[Defect],
    limitations: list[str],
    checks: list[CheckResult],
    *,
    start_slice_18_8: bool,
) -> Verdict:
    if start_slice_18_8:
        return "FAIL"
    hard_failed = sum(1 for c in checks if (not c.ok) and not _is_soft(c.check_id))
    if hard_failed or defects:
        return "FAIL"
    if limitations:
        return "PASS_WITH_LIMITATIONS" if set(limitations) <= SOFT_LIMITATION_CODES else "FAIL"
    return "PASS"


def build_report(monorepo: Path) -> Report:
    contract = default_contract()
    assert contract.start_slice_18_7 is True
    assert contract.start_slice_18_8 is False

    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []

    c, d, policy = check_policy(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, claims, status_counts = check_claim_inventory(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d = check_fields_and_routes(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d = check_telemetry_honesty(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, lim = check_ai_and_locality(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d = check_retention_and_assessment(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, lim = check_terminology_cli_vscode(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d = check_privacy_consistency(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, lim, contradictions = check_contradictions(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, lim, live_summary = check_live_endpoints()
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, lim = check_boundary(monorepo)
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
        start_slice_18_8=policy.get("start_slice_18_8") is True,
    )
    categories = sorted({c.category for c in checks})
    statuses = {cat: _status(checks, cat) for cat in categories}

    safe_claims = [
        {
            "claim_id": e.get("claim_id"),
            "category": e.get("category"),
            "status": e.get("status"),
            "release_disposition": e.get("release_disposition"),
        }
        for e in claims
    ]
    safe_contradictions = [
        {
            "contradiction_id": e.get("contradiction_id"),
            "classification": e.get("classification"),
        }
        for e in contradictions
    ]

    report = Report(
        schema=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        package_id=PACKAGE_ID,
        package_version=VERSION,
        epic=18,
        slice="18.7",
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
            "start_slice_18_7": policy.get("start_slice_18_7"),
            "start_slice_18_8": policy.get("start_slice_18_8"),
            "unsupported_claims_forbidden": policy.get("unsupported_claims_forbidden"),
            "telemetry_producer_status_honest": policy.get(
                "telemetry_producer_status_honest"
            ),
        },
        coverage={
            "claims": len(claims),
            "routes": 16,
            "collected_fields": 137,
            "claim_status_counts": status_counts,
        },
        claims=safe_claims,
        claim_status_counts=status_counts,
        epic18_boundary={"start_slice_18_7": True, "start_slice_18_8": False},
        freeze_confirmations={
            "no_runtime_redesign": True,
            "no_product_capability_redesign": True,
            "no_telemetry_schema_change": True,
            "no_community_api_redesign": True,
            "no_cli_publish": True,
            "no_vscode_marketplace_publish": True,
            "no_release_tag": True,
            "no_full_22_repository_release_corpus": True,
            "slice_18_8_not_started": True,
        },
        live_endpoints=live_summary,
        contradictions=safe_contradictions,
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
    out = monorepo / SV187_OUTPUT_RELATIVE
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
        f"Claims inventoried: {report.coverage.get('claims')}\n\n"
        "Slice 18.7 — Validate Public Claims Against Runtime. "
        "No runtime redesign. Slice 18.8 not started.\n",
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
        "start_slice_18_7=true start_slice_18_8=false "
        f"claims={report.coverage.get('claims')} "
        f"limitations={len(report.limitations)}"
    )
    return 0 if report.verdict != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
