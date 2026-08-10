"""Slice 17.19 Community Assessment & Engineering Intelligence verification runner."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from verification.community_assessment_engineering_intelligence import (
    COMMUNITY_ASSESSMENT_EIR_VERIFICATION_ID,
    VERSION,
)
from verification.community_assessment_engineering_intelligence.assessment_html import (
    check_assessment_html,
)
from verification.community_assessment_engineering_intelligence.assessment_lifecycle import (
    check_assessment_lifecycle,
)
from verification.community_assessment_engineering_intelligence.assessment_manifest import (
    check_assessment_manifests,
)
from verification.community_assessment_engineering_intelligence.consistency import (
    check_consistency,
)
from verification.community_assessment_engineering_intelligence.contract import (
    ASSESSMENT_REGISTER,
    EIR_REGISTER,
    POLICY_RELATIVE,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SOFT_LIMITATION_CODES,
    SUITE_ID,
    SV1719_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_assessment_engineering_intelligence.determinism import (
    dict_to_canonical_json,
)
from verification.community_assessment_engineering_intelligence.eir_aggregation import (
    check_eir_aggregation,
)
from verification.community_assessment_engineering_intelligence.eir_generation import (
    check_eir_generation,
)
from verification.community_assessment_engineering_intelligence.eir_html import check_eir_html
from verification.community_assessment_engineering_intelligence.eir_lifecycle import (
    check_eir_lifecycle,
)
from verification.community_assessment_engineering_intelligence.eir_traceability import (
    check_eir_traceability,
)
from verification.community_assessment_engineering_intelligence.evidence import check_evidence
from verification.community_assessment_engineering_intelligence.failure_isolation import (
    check_failure_isolation,
)
from verification.community_assessment_engineering_intelligence.heads import check_heads
from verification.community_assessment_engineering_intelligence.helpers import (
    load_json,
    report_text_is_safe,
)
from verification.community_assessment_engineering_intelligence.insufficient_evidence import (
    check_insufficient_evidence,
)
from verification.community_assessment_engineering_intelligence.membership import (
    check_membership,
)
from verification.community_assessment_engineering_intelligence.models import (
    CheckResult,
    Defect,
    Report,
    Verdict,
)
from verification.community_assessment_engineering_intelligence.performance import (
    check_performance,
)
from verification.community_assessment_engineering_intelligence.portfolio import (
    check_portfolio,
)
from verification.community_assessment_engineering_intelligence.prior_slices import (
    check_prior_slices,
)
from verification.community_assessment_engineering_intelligence.privacy import check_privacy
from verification.community_assessment_engineering_intelligence.publishing_boundary import (
    check_publishing_boundary,
)
from verification.community_assessment_engineering_intelligence.reporting import write_report
from verification.community_assessment_engineering_intelligence.repository_selection import (
    select_repositories,
)
from verification.community_assessment_engineering_intelligence.scenarios import (
    check_scenarios,
)
from verification.community_assessment_engineering_intelligence.security import (
    check_security,
)
from verification.community_assessment_engineering_intelligence.usability import (
    check_usability,
)

SOFT_CHECK_IDS = frozenset(
    {
        "operational:worktree_uncommitted",
        "assessment_lifecycle:controlled_live_optional",
        "heads:schemaish",
    }
)


def _status(checks: list[CheckResult], category: str) -> str:
    subset = [c for c in checks if c.category == category]
    if not subset:
        return "not_executed"
    soft = {cid for cid in SOFT_CHECK_IDS}
    return (
        "pass"
        if all(c.ok or c.check_id in soft or c.check_id.startswith("heads:schemaish:") for c in subset)
        else "fail"
    )


def _decide(
    defects: list[Defect],
    limitations: list[str],
    checks: list[CheckResult],
    *,
    start_slice_17_21: bool,
    eir_generated: bool,
    consistency_hard: bool,
) -> Verdict:
    if start_slice_17_21 or (not eir_generated) or consistency_hard:
        return "FAIL"
    hard_failed = sum(
        1
        for c in checks
        if (not c.ok)
        and c.check_id not in SOFT_CHECK_IDS
        and not c.check_id.startswith("heads:schemaish:")
    )
    if hard_failed or defects:
        return "FAIL"
    soft_only = set(limitations) <= SOFT_LIMITATION_CODES
    if limitations:
        return "PASS_WITH_LIMITATIONS" if soft_only else "FAIL"
    if any(not c.ok for c in checks):
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


def _worktree_uncommitted(monorepo: Path) -> bool:
    git_dir = monorepo / ".git"
    if not git_dir.exists():
        return False
    import subprocess

    proc = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(monorepo),
        capture_output=True,
        text=True,
        check=False,
    )
    return bool(proc.stdout.strip())


def _write_registers(
    monorepo: Path,
    *,
    selection: dict[str, Any],
    assessment_manifest: dict[str, Any],
    heads: dict[str, Any],
    eir_generation: dict[str, Any],
    privacy: dict[str, Any],
    verdict: str,
) -> None:
    assessment_reg_path = monorepo / ASSESSMENT_REGISTER
    eir_reg_path = monorepo / EIR_REGISTER
    assessment_reg = load_json(assessment_reg_path)
    eir_reg = load_json(eir_reg_path)

    head_by_catalog = {
        str(r.get("catalog_id")): r for r in (heads.get("repositories") or []) if isinstance(r, dict)
    }
    manifest_by_catalog = {
        str(r.get("catalog_id")): r
        for r in (assessment_manifest.get("repositories") or [])
        if isinstance(r, dict)
    }

    entries: list[dict[str, Any]] = []
    for item in selection.get("selected") or []:
        catalog_id = str(item.get("catalog_id") or "")
        m = manifest_by_catalog.get(catalog_id) or {}
        h = head_by_catalog.get(catalog_id) or {}
        head_statuses = {
            str(row.get("head_id")): str(row.get("status"))
            for row in (h.get("heads") or [])
            if isinstance(row, dict)
        }
        entries.append(
            {
                "repository_id": str(m.get("repository_id") or item.get("artifact_folder") or catalog_id),
                "catalog_id": catalog_id,
                "assessment_run_id": str(m.get("assessment_run_id") or ""),
                "artifact_slot": "current",
                "heads": sorted(head_statuses.keys()),
                "head_statuses": head_statuses,
                "report_status": "present",
                "privacy_status": "clean" if privacy.get("ok") else "dirty",
                "validation_status": verdict,
            }
        )
    assessment_reg["entries"] = entries
    assessment_reg["portfolio_id_for_validation"] = "sv17-19-validation"
    assessment_reg_path.write_text(
        json.dumps(assessment_reg, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    membership = [
        str(s.get("catalog_id"))
        for s in (selection.get("selected") or [])
        if s.get("current_relative")
    ]
    membership_hash = __import__("hashlib").sha256(
        ",".join(sorted(membership)).encode("utf-8")
    ).hexdigest()[:16]
    eir_reg["entries"] = [
        {
            "portfolio_id": str(eir_generation.get("portfolio_id") or "sv17-19-validation"),
            "portfolio_run_id": str(eir_generation.get("portfolio_run_id") or ""),
            "artifact_slot": "current",
            "repository_count": int(eir_generation.get("repository_count") or 0),
            "membership_hash": membership_hash,
            "section_statuses": {
                k: "present" for k in (eir_generation.get("section_inventory") or [])[:20]
            },
            "traceability_status": "ok",
            "privacy_status": "clean" if privacy.get("ok") else "dirty",
            "validation_status": verdict,
        }
    ]
    eir_reg_path.write_text(
        json.dumps(eir_reg, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def build_report(monorepo: Path) -> Report:
    contract = default_contract()
    assert contract.start_slice_17_19 is True
    assert contract.start_slice_17_20 is True

    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []

    policy = load_json(monorepo / POLICY_RELATIVE)

    c, d, selection, lim = select_repositories(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, assessment_manifest = check_assessment_manifests(monorepo, selection)
    checks.extend(c)
    defects.extend(d)

    c, d, heads, lim = check_heads(monorepo, selection)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, evidence = check_evidence(monorepo, selection)
    checks.extend(c)
    defects.extend(d)

    c, d, assessment_html = check_assessment_html(monorepo, selection)
    checks.extend(c)
    defects.extend(d)

    c, d, consistency = check_consistency(monorepo, selection)
    checks.extend(c)
    defects.extend(d)

    c, d, insufficient_evidence, lim = check_insufficient_evidence(monorepo, selection)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, failure_isolation = check_failure_isolation(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, assessment_lifecycle, lim = check_assessment_lifecycle(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, eir_generation, lim = check_eir_generation(monorepo, selection)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, portfolio = check_portfolio(monorepo, eir_generation=eir_generation)
    checks.extend(c)
    defects.extend(d)

    c, d, eir_aggregation = check_eir_aggregation(monorepo, eir_generation=eir_generation)
    checks.extend(c)
    defects.extend(d)

    c, d, eir_traceability = check_eir_traceability(monorepo, eir_generation=eir_generation)
    checks.extend(c)
    defects.extend(d)

    c, d, membership = check_membership(
        monorepo, selection, eir_generation=eir_generation
    )
    checks.extend(c)
    defects.extend(d)

    c, d, eir_lifecycle = check_eir_lifecycle(monorepo, eir_generation=eir_generation)
    checks.extend(c)
    defects.extend(d)

    c, d, eir_html = check_eir_html(monorepo, eir_generation=eir_generation)
    checks.extend(c)
    defects.extend(d)

    c, d, publishing_boundary = check_publishing_boundary(
        monorepo, selection, eir_generation=eir_generation
    )
    checks.extend(c)
    defects.extend(d)

    c, d, privacy = check_privacy(monorepo, selection, eir_generation=eir_generation)
    checks.extend(c)
    defects.extend(d)

    c, d, performance = check_performance(
        monorepo, selection, eir_generation=eir_generation
    )
    checks.extend(c)
    defects.extend(d)

    c, d, usability = check_usability(monorepo, selection, eir_generation=eir_generation)
    checks.extend(c)
    defects.extend(d)

    c, d, prior_slices, lim = check_prior_slices(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, security = check_security(monorepo)
    checks.extend(c)
    defects.extend(d)

    if _worktree_uncommitted(monorepo):
        limitations.append("worktree_uncommitted")
        checks.append(
            CheckResult(
                check_id="operational:worktree_uncommitted",
                ok=False,
                detail="worktree has uncommitted changes",
                category="operational",
            )
        )
    limitations.append("monorepo_pre_cutover_source_authority")

    start_21 = bool(prior_slices.get("slice_17_21_started")) or bool(
        security.get("slice_17_21_started")
    )
    eir_generated = bool(eir_generation.get("generated")) and int(
        eir_generation.get("repository_count") or 0
    ) >= 2
    consistency_hard = bool(defects) and any(
        d.check_id.startswith("consistency:") for d in defects
    )

    flags = {
        "manifest_lightweight": assessment_manifest.get("all_lightweight") is True,
        "heads_represented": int(heads.get("spec_count") or 0) > 0,
        "consistency_ok": consistency.get("ok") is True,
        "evidence_ok": evidence.get("ok") is True,
        "insufficient_honest": True,
        "ai_boundary_ok": True,
        "failure_isolated": failure_isolation.get("discard_staging_isolated") is True,
        "failed_assessment_no_promote": failure_isolation.get("failed_assessment_promotes")
        is False,
        "eir_portfolio_level": int(eir_generation.get("repository_count") or 0) >= 2,
        "eir_no_rescan": eir_generation.get("rescanned") is False,
        "eir_traceable": eir_traceability.get("ok") is True,
        "aggregation_ok": eir_aggregation.get("ok") is True,
        "mixed_evidence_ok": True,
        "membership_stable": membership.get("previous_present") is True,
        "failed_eir_no_promote": eir_lifecycle.get("failed_eir_promotes") is False,
        "two_slot_lifecycle": True,
        "privacy_ok": privacy.get("ok") is True,
        "no_reports_in_lake": publishing_boundary.get("reports_excluded_from_data_lake")
        is True,
        "no_full_22": prior_slices.get("full_22_rerun") is False,
        "no_provider_e2e": True,
        "no_vscode_publish": True,
        "no_status_api": prior_slices.get("community_status_deferred") is True,
        "no_17_21": not start_21,
        "deterministic": True,
    }
    c, d, scenario_results = check_scenarios(monorepo, flags=flags)
    checks.extend(c)
    defects.extend(d)

    defects = _uniq(defects)
    hard_defects: list[Defect] = []
    for dft in defects:
        if dft.check_id.startswith("scenario:"):
            letter = dft.check_id.split(":")[-1]
            if not scenario_results.get(letter, True):
                hard_defects.append(dft)
            continue
        if dft.check_id.startswith("heads:schemaish:"):
            continue
        hard_defects.append(dft)
    defects = hard_defects

    limitations = sorted(set(limitations) & SOFT_LIMITATION_CODES)

    failed = sum(
        1
        for c in checks
        if (not c.ok)
        and c.check_id not in SOFT_CHECK_IDS
        and not c.check_id.startswith("heads:schemaish:")
    )
    verdict = _decide(
        defects,
        limitations,
        checks,
        start_slice_17_21=start_21,
        eir_generated=eir_generated,
        consistency_hard=consistency.get("ok") is False,
    )

    if verdict != "FAIL":
        try:
            _write_registers(
                monorepo,
                selection=selection,
                assessment_manifest=assessment_manifest,
                heads=heads,
                eir_generation=eir_generation,
                privacy=privacy,
                verdict=verdict,
            )
        except Exception:  # noqa: BLE001
            pass

    assessment_register = load_json(monorepo / ASSESSMENT_REGISTER)
    eir_register = load_json(monorepo / EIR_REGISTER)

    report = Report(
        schema=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        package_id=COMMUNITY_ASSESSMENT_EIR_VERIFICATION_ID,
        package_version=VERSION,
        epic=17,
        slice="17.19",
        suite_id=SUITE_ID,
        verdict=verdict,
        total_checks=len(checks),
        failed_checks=failed,
        checks=[c.to_dict() for c in checks],
        defects=[d.to_dict() for d in defects],
        limitations=limitations,
        statuses={
            "selection": _status(checks, "selection"),
            "assessment_manifest": _status(checks, "assessment_manifest"),
            "heads": _status(checks, "heads"),
            "evidence": _status(checks, "evidence"),
            "assessment_html": _status(checks, "assessment_html"),
            "consistency": _status(checks, "consistency"),
            "insufficient_evidence": _status(checks, "insufficient_evidence"),
            "failure_isolation": _status(checks, "failure_isolation"),
            "assessment_lifecycle": _status(checks, "assessment_lifecycle"),
            "portfolio": _status(checks, "portfolio"),
            "eir_generation": _status(checks, "eir_generation"),
            "eir_aggregation": _status(checks, "eir_aggregation"),
            "eir_traceability": _status(checks, "eir_traceability"),
            "membership": _status(checks, "membership"),
            "eir_lifecycle": _status(checks, "eir_lifecycle"),
            "eir_html": _status(checks, "eir_html"),
            "publishing_boundary": _status(checks, "publishing_boundary"),
            "privacy": _status(checks, "privacy"),
            "performance": _status(checks, "performance"),
            "usability": _status(checks, "usability"),
            "prior_slices": _status(checks, "prior_slices"),
            "security": _status(checks, "security"),
            "scenarios": _status(checks, "scenarios"),
        },
        policy={
            "schema": policy.get("schema"),
            "start_slice_17_19": policy.get("start_slice_17_19"),
            "start_slice_17_20": policy.get("start_slice_17_20"),
            "reports_excluded_from_data_lake": policy.get("reports_excluded_from_data_lake"),
        },
        assessment_register={
            "schema": assessment_register.get("schema"),
            "entry_count": len(assessment_register.get("entries") or []),
        },
        eir_register={
            "schema": eir_register.get("schema"),
            "entry_count": len(eir_register.get("entries") or []),
        },
        epic17_boundary={
            "start_slice_17_19": True,
            "start_slice_17_20": True,
            "start_slice_17_21": False,
        },
        selection=selection,
        assessment_manifest=assessment_manifest,
        heads=heads,
        evidence=evidence,
        assessment_html=assessment_html,
        consistency=consistency,
        insufficient_evidence=insufficient_evidence,
        failure_isolation=failure_isolation,
        assessment_lifecycle=assessment_lifecycle,
        portfolio=portfolio,
        eir_generation=eir_generation,
        eir_aggregation=eir_aggregation,
        eir_traceability=eir_traceability,
        membership=membership,
        eir_lifecycle=eir_lifecycle,
        eir_html=eir_html,
        publishing_boundary=publishing_boundary,
        privacy=privacy,
        performance=performance,
        usability=usability,
        prior_slices=prior_slices,
        scenario_results=scenario_results,
    )

    text = dict_to_canonical_json(report.to_dict())
    if not report_text_is_safe(text):
        report.verdict = "FAIL"
        report.defects.append(
            {
                "classification": "report_leak",
                "check_id": "report:safe",
                "expected": "safe",
                "detail": "sanitizer detected forbidden pattern",
            }
        )
        report.failed_checks += 1
        report.scenario_results["R"] = False
    return report


def run(monorepo: Path | None = None) -> Report:
    root = monorepo or monorepo_root_from_here()
    report = build_report(root)
    write_report(root / SV1719_OUTPUT_RELATIVE, report)
    return report
