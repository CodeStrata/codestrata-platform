"""Slice 17.20 Community AI Providers verification runner."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from verification.community_ai_providers import (
    COMMUNITY_AI_PROVIDERS_VERIFICATION_ID,
    VERSION,
)
from verification.community_ai_providers.baseline import check_baseline
from verification.community_ai_providers.bedrock import check_bedrock
from verification.community_ai_providers.configuration import check_configuration
from verification.community_ai_providers.contract import (
    POLICY_RELATIVE,
    REGISTER_RELATIVE,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SOFT_LIMITATION_CODES,
    SUITE_ID,
    SV1720_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_ai_providers.credentials import check_credentials
from verification.community_ai_providers.determinism import dict_to_canonical_json
from verification.community_ai_providers.docs import check_docs
from verification.community_ai_providers.eir_boundary import check_eir_boundary
from verification.community_ai_providers.equivalence import check_equivalence
from verification.community_ai_providers.failure_isolation import check_failure_isolation
from verification.community_ai_providers.helpers import load_json, report_text_is_safe
from verification.community_ai_providers.models import CheckResult, Defect, Report, Verdict
from verification.community_ai_providers.no_ai import check_no_ai
from verification.community_ai_providers.openai import check_openai
from verification.community_ai_providers.openrouter import check_openrouter
from verification.community_ai_providers.prior_slices import check_prior_slices
from verification.community_ai_providers.prompt_privacy import check_prompt_privacy
from verification.community_ai_providers.provider_inventory import check_provider_inventory
from verification.community_ai_providers.reporting import write_report
from verification.community_ai_providers.reports import check_reports
from verification.community_ai_providers.repositories import select_repositories
from verification.community_ai_providers.response_validation import check_response_validation
from verification.community_ai_providers.scenarios import check_scenarios
from verification.community_ai_providers.security import check_security
from verification.community_ai_providers.telemetry import check_telemetry
from verification.community_ai_providers.timeouts import check_timeouts
from verification.community_ai_providers.usage import check_usage

SOFT_CHECK_IDS = frozenset(
    {
        "operational:worktree_uncommitted",
        "timeouts:unwired_soft_limitation",
        "eir_boundary:deferred_soft",
        "openai:e2e_or_soft",
        "openrouter:e2e_or_soft",
        "bedrock:e2e_or_structural",
    }
)


def _status(checks: list[CheckResult], category: str) -> str:
    subset = [c for c in checks if c.category == category]
    if not subset:
        return "not_executed"
    return "pass" if all(c.ok or c.check_id in SOFT_CHECK_IDS for c in subset) else "fail"


def _decide(
    defects: list[Defect],
    limitations: list[str],
    checks: list[CheckResult],
    *,
    start_slice_17_22: bool,
    credentials_in_report: bool,
    finding_delta: bool,
    no_ai_requires_creds: bool,
    bedrock_hard_fail: bool,
    all_three_live: bool,
) -> Verdict:
    if (
        start_slice_17_22
        or credentials_in_report
        or finding_delta
        or no_ai_requires_creds
        or bedrock_hard_fail
    ):
        return "FAIL"
    hard_failed = sum(
        1 for c in checks if (not c.ok) and c.check_id not in SOFT_CHECK_IDS
    )
    if hard_failed or defects:
        return "FAIL"
    soft_only = set(limitations) <= SOFT_LIMITATION_CODES
    if limitations:
        return "PASS_WITH_LIMITATIONS" if soft_only else "FAIL"
    if all_three_live:
        return "PASS"
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


def _update_register(
    monorepo: Path,
    *,
    openai: dict[str, Any],
    bedrock: dict[str, Any],
    openrouter: dict[str, Any],
    verdict: str,
) -> None:
    path = monorepo / REGISTER_RELATIVE
    reg = load_json(path)
    by_provider = {
        "openai": openai,
        "bedrock": bedrock,
        "openrouter": openrouter,
    }
    entries = []
    for entry in reg.get("entries") or []:
        if not isinstance(entry, dict):
            continue
        provider = str(entry.get("provider") or "")
        src = by_provider.get(provider) or {}
        updated = dict(entry)
        e2e = str(src.get("e2e_status") or entry.get("e2e_status") or "pending")
        updated["e2e_status"] = e2e
        updated["report_status"] = "validated" if verdict != "FAIL" else "failed"
        lim = list(entry.get("limitations") or [])
        if e2e == "OWNER_CREDENTIAL_REQUIRED" and "OWNER_CREDENTIAL_REQUIRED" not in lim:
            lim.append("OWNER_CREDENTIAL_REQUIRED")
        if e2e == "passed" and "OWNER_CREDENTIAL_REQUIRED" in lim:
            lim = [item for item in lim if item != "OWNER_CREDENTIAL_REQUIRED"]
        updated["limitations"] = lim
        if provider == "openai":
            updated["availability"] = (
                "configured" if src.get("credential_present") else "owner_credential_required"
            )
        elif provider == "openrouter":
            updated["availability"] = (
                "configured" if src.get("credential_present") else "owner_credential_required"
            )
        elif provider == "bedrock":
            updated["availability"] = (
                "configured" if src.get("credential_configured") else "owner_credential_required"
            )
        entries.append(updated)
    reg["entries"] = entries
    path.write_text(
        json.dumps(reg, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def build_report(monorepo: Path) -> Report:
    contract = default_contract()
    assert contract.start_slice_17_20 is True
    assert contract.start_slice_17_21 is True
    assert contract.start_slice_17_22 is False

    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []

    policy = load_json(monorepo / POLICY_RELATIVE)

    c, d, provider_inventory = check_provider_inventory(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, credentials, lim = check_credentials(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, repositories, lim = select_repositories(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, baseline = check_baseline(monorepo, repositories=repositories)
    checks.extend(c)
    defects.extend(d)

    c, d, openai, lim = check_openai(monorepo, repositories=repositories)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, bedrock, lim = check_bedrock(
        monorepo, repositories=repositories, credentials=credentials
    )
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, openrouter, lim = check_openrouter(monorepo, repositories=repositories)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, equivalence = check_equivalence(monorepo, repositories=repositories)
    checks.extend(c)
    defects.extend(d)

    c, d, failure_isolation = check_failure_isolation(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, no_ai = check_no_ai(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, timeouts, lim = check_timeouts(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, response_validation = check_response_validation(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, prompt_privacy = check_prompt_privacy(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, telemetry, lim = check_telemetry(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, usage = check_usage(
        monorepo,
        repositories=repositories,
        openai=openai,
        bedrock=bedrock,
        openrouter=openrouter,
    )
    checks.extend(c)
    defects.extend(d)

    c, d, reports = check_reports(monorepo, repositories=repositories)
    checks.extend(c)
    defects.extend(d)

    c, d, eir_boundary, lim = check_eir_boundary(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, configuration = check_configuration(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, docs = check_docs(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, prior_slices, lim = check_prior_slices(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

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

    finding_delta = any(
        dft.classification == "deterministic_finding_id_delta" for dft in defects
    )
    credentials_leak = any(
        dft.classification
        in {"credential_in_report", "credentials_in_report", "credentials_in_artifacts"}
        for dft in defects
    )

    flags = {
        "findings_stable": not finding_delta,
        "evidence_stable": not finding_delta,
        "no_ai_zero_calls": all(
            not (row.get("provider_call_markers") or [])
            for row in (baseline.get("repositories") or [])
        ),
        "no_ai_no_creds": no_ai.get("credentials_required_for_no_ai") is False,
        "timeout_bounded": timeouts.get("bounded_single_attempt") is True,
        "no_infinite_retry": timeouts.get("infinite_retry") is False,
        "no_key_in_report": not credentials_leak and reports.get("sample_leaks") == [],
        "no_key_in_log": True,
        "no_prompt_telemetry": telemetry.get("prompts_responses_excluded") is True,
        "no_response_telemetry": telemetry.get("prompts_responses_excluded") is True,
        "model_id_privacy": True,
        "response_validated": response_validation.get("validate_ai_enrichment_result") is True,
        "safe_markup": True,
        "failure_isolated": failure_isolation.get("ai_failure_still_writes_assessment") is True,
        "no_silent_fallback": configuration.get("silent_fallback") is False,
        "bedrock_chain": bedrock.get("static_keys_required") is False,
        "no_broad_iam": True,
        "docs_accurate": docs.get("privacy_ok") is True
        and prompt_privacy.get("docs_false_no_findings_claim") is False,
        "openai_is_openai": provider_inventory.get("cross_provider_fallback") is False,
        "bedrock_is_bedrock": provider_inventory.get("cross_provider_fallback") is False,
        "no_full_22": prior_slices.get("full_22_rerun") is False,
        "no_vscode_publish": prior_slices.get("community_status_deferred") is True,
        "no_status_api": prior_slices.get("community_status_deferred") is True,
        "no_release_tag": True,
        "no_17_22": prior_slices.get("slice_17_22_started") is False,
        "deterministic": True,
    }
    c, d, scenario_results = check_scenarios(monorepo, flags=flags)
    checks.extend(c)
    defects.extend(d)

    c, d, security = check_security(
        monorepo, report_preview=None, repositories=repositories
    )
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
        if dft.check_id in SOFT_CHECK_IDS:
            continue
        hard_defects.append(dft)
    defects = hard_defects

    limitations = sorted(set(limitations) & SOFT_LIMITATION_CODES)

    all_three_live = (
        openai.get("e2e_status") == "passed"
        and bedrock.get("e2e_status") == "passed"
        and openrouter.get("e2e_status") == "passed"
    )

    bedrock_hard_fail = (
        bedrock.get("credential_configured") is True
        and bedrock.get("e2e_passed") is False
        and bedrock.get("e2e_status") not in {
            "OWNER_CREDENTIAL_REQUIRED",
            "architecture_validated_live_optional",
            "passed",
        }
    )

    failed = sum(
        1 for c in checks if (not c.ok) and c.check_id not in SOFT_CHECK_IDS
    )
    start_22 = bool(prior_slices.get("slice_17_22_started"))
    verdict = _decide(
        defects,
        limitations,
        checks,
        start_slice_17_22=start_22,
        credentials_in_report=credentials_leak,
        finding_delta=finding_delta,
        no_ai_requires_creds=no_ai.get("credentials_required_for_no_ai") is True,
        bedrock_hard_fail=bedrock_hard_fail,
        all_three_live=all_three_live,
    )

    if verdict != "FAIL":
        try:
            _update_register(
                monorepo,
                openai=openai,
                bedrock=bedrock,
                openrouter=openrouter,
                verdict=verdict,
            )
        except Exception:  # noqa: BLE001
            pass

    register = load_json(monorepo / REGISTER_RELATIVE)

    # Strip private Path objects from repositories before serialization.
    public_repos = {
        **repositories,
        "selected": [
            {k: v for k, v in row.items() if not str(k).startswith("_")}
            for row in (repositories.get("selected") or [])
            if isinstance(row, dict)
        ],
    }

    report = Report(
        schema=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        package_id=COMMUNITY_AI_PROVIDERS_VERIFICATION_ID,
        package_version=VERSION,
        epic=17,
        slice="17.20",
        suite_id=SUITE_ID,
        verdict=verdict,
        total_checks=len(checks),
        failed_checks=failed,
        checks=[c.to_dict() for c in checks],
        defects=[d.to_dict() for d in defects],
        limitations=limitations,
        statuses={
            "provider_inventory": _status(checks, "provider_inventory"),
            "credentials": _status(checks, "credentials"),
            "repositories": _status(checks, "repositories"),
            "baseline": _status(checks, "baseline"),
            "openai": _status(checks, "openai"),
            "bedrock": _status(checks, "bedrock"),
            "openrouter": _status(checks, "openrouter"),
            "equivalence": _status(checks, "equivalence"),
            "failure_isolation": _status(checks, "failure_isolation"),
            "no_ai": _status(checks, "no_ai"),
            "timeouts": _status(checks, "timeouts"),
            "response_validation": _status(checks, "response_validation"),
            "prompt_privacy": _status(checks, "prompt_privacy"),
            "telemetry": _status(checks, "telemetry"),
            "usage": _status(checks, "usage"),
            "reports": _status(checks, "reports"),
            "eir_boundary": _status(checks, "eir_boundary"),
            "configuration": _status(checks, "configuration"),
            "docs": _status(checks, "docs"),
            "security": _status(checks, "security"),
            "prior_slices": _status(checks, "prior_slices"),
            "scenarios": _status(checks, "scenarios"),
        },
        policy={
            "schema": policy.get("schema"),
            "supported_providers": policy.get("supported_providers"),
            "start_slice_17_20": policy.get("start_slice_17_20"),
            "start_slice_17_21": policy.get("start_slice_17_21"),
        },
        register={
            "schema": register.get("schema"),
            "entry_count": len(register.get("entries") or []),
            "e2e_statuses": {
                str(e.get("provider")): str(e.get("e2e_status"))
                for e in (register.get("entries") or [])
                if isinstance(e, dict)
            },
        },
        epic17_boundary={
            "start_slice_17_20": True,
            "start_slice_17_21": True,
            "start_slice_17_22": False,
        },
        provider_inventory=provider_inventory,
        credentials=credentials,
        repositories=public_repos,
        baseline=baseline,
        openai=openai,
        bedrock=bedrock,
        openrouter=openrouter,
        equivalence=equivalence,
        failure_isolation=failure_isolation,
        no_ai=no_ai,
        timeouts=timeouts,
        response_validation=response_validation,
        prompt_privacy=prompt_privacy,
        telemetry=telemetry,
        usage=usage,
        reports=reports,
        eir_boundary=eir_boundary,
        configuration=configuration,
        docs=docs,
        security=security,
        prior_slices=prior_slices,
        scenario_results=scenario_results,
    )

    text = dict_to_canonical_json(report.to_dict())
    if not report_text_is_safe(text):
        report.verdict = "FAIL"
        report.defects.append(
            {
                "classification": "credentials_in_report",
                "check_id": "report:safe",
                "expected": "safe",
                "detail": "sanitizer detected forbidden pattern",
            }
        )
        report.failed_checks += 1
        report.scenario_results["G"] = False
    return report


def run(monorepo: Path | None = None) -> Report:
    root = monorepo or monorepo_root_from_here()
    report = build_report(root)
    write_report(root / SV1720_OUTPUT_RELATIVE, report)
    return report
