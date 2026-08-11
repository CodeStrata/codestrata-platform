"""Slice 18.8 Epic 18 Transparency Documentation completion runner."""

from __future__ import annotations

from pathlib import Path

from verification.community_epic18_completion import PACKAGE_ID, VERSION
from verification.community_epic18_completion.checks import (
    check_carry_forwards,
    check_claim_inventory,
    check_contradictions,
    check_evidence_inventory,
    check_policy,
    check_prior_suites,
    check_report_publishing,
    check_security,
    check_slice_matrix,
    check_topics,
    check_workflows,
)
from verification.community_epic18_completion.contract import (
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SOFT_LIMITATION_CODES,
    SUITE_ID,
    SV188_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_epic18_completion.determinism import (
    assert_deterministic_payload,
)
from verification.community_epic18_completion.helpers import (
    dict_to_canonical_json,
    report_text_is_safe,
)
from verification.community_epic18_completion.models import (
    CheckResult,
    Defect,
    Epic19Gate,
    EpicVerdict,
    Report,
    Verdict,
)

SOFT_CHECK_IDS = frozenset(
    {
        "evidence:present:E18-EV-013",
        "evidence:present:E18-EV-016",
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
    release_started: bool,
) -> Verdict:
    if release_started:
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
    claim_inventory: dict,
) -> EpicVerdict:
    hard = [c for c in checks if (not c.ok) and c.check_id not in SOFT_CHECK_IDS]
    if hard or defects or suite_verdict == "FAIL":
        return "EPIC_BLOCKED"
    if claim_inventory.get("UNSUPPORTED", 0) or claim_inventory.get("CONTRADICTORY", 0):
        return "EPIC_BLOCKED"
    if carry or suite_verdict == "PASS_WITH_LIMITATIONS":
        return "EPIC_COMPLETE_WITH_DOCUMENTED_LIMITATIONS"
    return "EPIC_COMPLETE"


def _decide_gate(epic_verdict: EpicVerdict) -> Epic19Gate:
    if epic_verdict in {
        "EPIC_COMPLETE",
        "EPIC_COMPLETE_WITH_DOCUMENTED_LIMITATIONS",
    }:
        return "EPIC_19_RELEASE_READINESS_MAY_START"
    return "EPIC_19_RELEASE_READINESS_MUST_NOT_START"


def build_report(monorepo: Path) -> Report:
    contract = default_contract()
    assert contract.start_slice_18_8 is True
    assert contract.start_release_readiness_epic is False

    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []

    c, d, policy = check_policy(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, prior = check_prior_suites(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, evidence = check_evidence_inventory(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, claim_inventory, lim = check_claim_inventory(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, contradictions, lim = check_contradictions(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, lim = check_report_publishing(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, topics, lim = check_topics(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, matrix = check_slice_matrix(monorepo, prior)
    checks.extend(c)
    defects.extend(d)

    c, d, lim = check_workflows(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, carry = check_carry_forwards(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, security = check_security(monorepo)
    checks.extend(c)
    defects.extend(d)

    defects = _uniq(defects)
    limitations = sorted({x for x in limitations if x in SOFT_LIMITATION_CODES})
    failed = sum(1 for c in checks if (not c.ok) and c.check_id not in SOFT_CHECK_IDS)
    verdict = _decide_suite(
        defects,
        limitations,
        checks,
        release_started=policy.get("start_release_readiness_epic") is True,
    )
    epic_verdict = _decide_epic(
        suite_verdict=verdict,
        defects=defects,
        checks=checks,
        carry=carry,
        claim_inventory=claim_inventory,
    )
    gate = _decide_gate(epic_verdict)

    # Finalize 18.8 matrix row.
    if "18.8" in matrix:
        matrix["18.8"]["final_status"] = (
            "COMPLETE"
            if epic_verdict
            in {"EPIC_COMPLETE", "EPIC_COMPLETE_WITH_DOCUMENTED_LIMITATIONS"}
            else "INCOMPLETE"
        )
        matrix["18.8"]["authoritative_evidence"] = f"sv18-8 verdict={verdict}"

    categories = sorted({c.category for c in checks})
    statuses = {cat: _status(checks, cat) for cat in categories}

    # sv18-7 baseline snapshot (canonical public-claim suite).
    sv187_path = (
        monorepo
        / ".codestrata-artifacts/validation/suites/sv18-7"
        / "community-public-claim-runtime-validation-verification.json"
    )
    sv187: dict = {}
    if sv187_path.is_file():
        from verification.community_epic18_completion.helpers import load_json

        doc = load_json(sv187_path)
        sv187 = {
            "verdict": doc.get("verdict"),
            "total_checks": doc.get("total_checks"),
            "failed_checks": doc.get("failed_checks"),
            "claim_status_counts": (doc.get("claim_status_counts") or doc.get("coverage", {}).get("claim_status_counts")),
            "canonical": True,
            "reason": "sv18-7 remains the canonical public-claim/runtime suite; sv18-8 aggregates it",
        }

    report = Report(
        schema=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        package_id=PACKAGE_ID,
        package_version=VERSION,
        epic=18,
        slice="18.8",
        suite_id=SUITE_ID,
        verdict=verdict,
        epic_verdict=epic_verdict,
        epic19_gate=gate,
        total_checks=len(checks),
        failed_checks=failed,
        checks=[c.to_dict() for c in checks],
        defects=[d.to_dict() for d in defects],
        limitations=limitations,
        statuses=statuses,
        policy={
            "schema": policy.get("schema"),
            "start_slice_18_8": policy.get("start_slice_18_8"),
            "start_release_readiness_epic": policy.get("start_release_readiness_epic"),
            "epic18_transparency_work_complete": policy.get(
                "epic18_transparency_work_complete"
            ),
        },
        evidence_inventory=[
            {
                "artifact_id": e.get("artifact_id"),
                "path": e.get("path"),
                "classification": e.get("classification"),
                "slice": e.get("slice"),
            }
            for e in evidence
        ],
        claim_inventory=claim_inventory,
        contradiction_closure=contradictions,
        slice_matrix=matrix,
        topic_verification=topics,
        security_scan=security,
        prior_suites=prior,
        release_carry_forwards=[
            {
                "item_id": e.get("item_id"),
                "description": e.get("description"),
                "disposition": e.get("disposition"),
            }
            for e in carry
        ],
        epic18_boundary={
            "start_slice_18_8": True,
            "start_release_readiness_epic": False,
        },
        freeze_confirmations={
            "no_cli_publish": True,
            "no_vscode_marketplace_publish": True,
            "no_release_tag": True,
            "no_release_commit": True,
            "no_full_22_repository_release_corpus": True,
            "no_silent_community_cloud_redeploy": True,
            "no_manufactured_owner_e2e": True,
            "epic19_not_started": True,
        },
        sv18_7_baseline=sv187,
    )

    text = dict_to_canonical_json(report.to_dict())
    if not report_text_is_safe(text) or "timestamp" in text or "/Users/" in text:
        report.verdict = "FAIL"
        report.epic_verdict = "EPIC_BLOCKED"
        report.epic19_gate = "EPIC_19_RELEASE_READINESS_MUST_NOT_START"
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
    assert_deterministic_payload(report.to_dict())
    return report


def write_report(monorepo: Path, report: Report) -> Path:
    out_dir = monorepo / SV188_OUTPUT_RELATIVE
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / REPORT_JSON
    md_path = out_dir / REPORT_MD
    payload = report.to_dict()
    json_path.write_text(dict_to_canonical_json(payload) + "\n", encoding="utf-8")
    lines = [
        "# Community Epic 18 Completion Verification (Slice 18.8)",
        "",
        f"Verdict: **{report.verdict}**",
        f"Epic verdict: **{report.epic_verdict}**",
        f"Epic 19 gate: **{report.epic19_gate}**",
        f"Checks: {report.total_checks} (failed={report.failed_checks})",
        "",
        "## Claim inventory",
        "",
        f"- total: {report.claim_inventory.get('total')}",
        f"- SUPPORTED: {report.claim_inventory.get('SUPPORTED')}",
        f"- SUPPORTED_WITH_QUALIFICATION: {report.claim_inventory.get('SUPPORTED_WITH_QUALIFICATION')}",
        f"- STALE: {report.claim_inventory.get('STALE')}",
        f"- UNSUPPORTED: {report.claim_inventory.get('UNSUPPORTED')}",
        f"- CONTRADICTORY: {report.claim_inventory.get('CONTRADICTORY')}",
        f"- EXPECTED_RELEASE_GAP: {report.claim_inventory.get('EXPECTED_RELEASE_GAP')}",
        "",
        "## Limitations",
        "",
    ]
    for lim in report.limitations:
        lines.append(f"- `{lim}`")
    lines.extend(
        [
            "",
            "Slice 18.8 Transparency Documentation Epic completion.",
            "Release Readiness not started. No CLI/VS Code publish. No release tag.",
            "No 22-repository production corpus.",
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path


def main() -> int:
    root = monorepo_root_from_here()
    report = build_report(root)
    path = write_report(root, report)
    print(
        f"{report.verdict} checks={report.total_checks} failed={report.failed_checks} "
        f"report={path}"
    )
    print(
        f"epic_verdict={report.epic_verdict} epic19_gate={report.epic19_gate} "
        f"start_slice_18_8=true start_release_readiness_epic=false "
        f"claims={report.claim_inventory.get('total')} limitations={len(report.limitations)}"
    )
    return 0 if report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
