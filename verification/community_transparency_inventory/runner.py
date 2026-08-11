"""Slice 18.1 Community Transparency Inventory runner."""

from __future__ import annotations

from pathlib import Path

from verification.community_transparency_inventory import PACKAGE_ID, VERSION
from verification.community_transparency_inventory.checks import (
    check_ai_providers,
    check_assessment_eir_publish_insights,
    check_boundary_and_worktree,
    check_consent_and_identity,
    check_destinations_retention_locality,
    check_never_collected,
    check_policy,
    check_registers_present,
    check_runtime_field_coverage,
    check_runtime_route_coverage,
    check_streams,
    check_topics_docs_contradictions,
)
from verification.community_transparency_inventory.contract import (
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SOFT_LIMITATION_CODES,
    SUITE_ID,
    SV181_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_transparency_inventory.determinism import (
    assert_deterministic_payload,
)
from verification.community_transparency_inventory.helpers import (
    dict_to_canonical_json,
    report_text_is_safe,
)
from verification.community_transparency_inventory.models import (
    CheckResult,
    Defect,
    Report,
    Verdict,
)

SOFT_CHECK_IDS = frozenset({"api:legacy_register_stale_noted"})


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
    start_slice_18_2: bool,
) -> Verdict:
    if start_slice_18_2:
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
    assert contract.start_slice_18_1 is True
    assert contract.start_slice_18_2 is False

    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []

    c, d, policy = check_policy(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, regs = check_registers_present(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, field_cov = check_runtime_field_coverage(monorepo, regs.get("fields") or {})
    checks.extend(c)
    defects.extend(d)

    c, d, route_cov, lim = check_runtime_route_coverage(monorepo, regs.get("api") or {})
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, lim = check_streams(regs.get("streams") or {})
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d = check_never_collected(regs.get("never_collected") or {})
    checks.extend(c)
    defects.extend(d)

    c, d = check_consent_and_identity(regs.get("consent") or {}, regs.get("identity") or {})
    checks.extend(c)
    defects.extend(d)

    c, d = check_destinations_retention_locality(
        regs.get("destinations") or {},
        regs.get("retention") or {},
        regs.get("source_locality") or {},
    )
    checks.extend(c)
    defects.extend(d)

    c, d, lim = check_ai_providers(regs.get("ai") or {})
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d = check_assessment_eir_publish_insights(
        regs.get("assessment") or {},
        regs.get("eir") or {},
        regs.get("publishing") or {},
        regs.get("insights") or {},
        regs.get("opt_out") or {},
    )
    checks.extend(c)
    defects.extend(d)

    c, d, lim = check_topics_docs_contradictions(
        regs.get("topic") or {},
        regs.get("public_docs") or {},
        regs.get("contradictions") or {},
        regs.get("doc_authority") or {},
    )
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, lim = check_boundary_and_worktree(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    defects = _uniq(defects)
    limitations = sorted({x for x in limitations if x in SOFT_LIMITATION_CODES})
    failed = sum(1 for c in checks if (not c.ok) and c.check_id not in SOFT_CHECK_IDS)
    verdict = _decide(
        defects,
        limitations,
        checks,
        start_slice_18_2=policy.get("start_slice_18_2") is True,
    )
    categories = sorted({c.category for c in checks})
    statuses = {cat: _status(checks, cat) for cat in categories}
    contra_entries = (regs.get("contradictions") or {}).get("entries") or []

    report = Report(
        schema=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        package_id=PACKAGE_ID,
        package_version=VERSION,
        epic=18,
        slice="18.1",
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
            "runtime_is_documentation_source_of_truth": policy.get(
                "runtime_is_documentation_source_of_truth"
            ),
            "start_slice_18_1": policy.get("start_slice_18_1"),
            "start_slice_18_2": policy.get("start_slice_18_2"),
            "no_runtime_redesign": policy.get("no_runtime_redesign"),
        },
        coverage={
            "registers": sorted(regs.keys()),
            "fields": field_cov,
            "routes": route_cov,
        },
        contradictions=[
            {
                "contradiction_id": e.get("contradiction_id"),
                "classification": e.get("classification"),
            }
            for e in contra_entries
            if isinstance(e, dict)
        ],
        epic18_boundary={"start_slice_18_1": True, "start_slice_18_2": False},
        freeze_confirmations={
            "no_runtime_redesign": True,
            "no_cli_publish": True,
            "no_vscode_marketplace_publish": True,
            "no_release_tag": True,
            "no_full_22_repository_release_corpus": True,
            "slice_18_2_not_started": True,
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
    out = monorepo / SV181_OUTPUT_RELATIVE
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
        "Slice 18.1 — Authoritative Transparency Inventory. "
        "Runtime is documentation source of truth. Slice 18.2 not started.\n",
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
        "start_slice_18_1=true start_slice_18_2=false "
        f"limitations={len(report.limitations)} registers={len(report.coverage.get('registers') or [])}"
    )
    return 0 if report.verdict != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
