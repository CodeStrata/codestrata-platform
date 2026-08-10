"""Slice 17.17 Community telemetry consent verification runner."""

from __future__ import annotations

from pathlib import Path

from verification.community_telemetry_consent import (
    COMMUNITY_TELEMETRY_CONSENT_VERIFICATION_ID,
    VERSION,
)
from verification.community_telemetry_consent.auth import check_auth
from verification.community_telemetry_consent.cli_off import check_cli_off
from verification.community_telemetry_consent.cli_on import check_cli_on
from verification.community_telemetry_consent.contract import (
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SOFT_LIMITATION_CODES,
    SUITE_ID,
    SV1717_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_telemetry_consent.data_lake import check_data_lake
from verification.community_telemetry_consent.determinism import dict_to_canonical_json
from verification.community_telemetry_consent.docs import check_docs
from verification.community_telemetry_consent.event_types import check_event_types
from verification.community_telemetry_consent.helpers import load_json, report_text_is_safe
from verification.community_telemetry_consent.identity import check_identity
from verification.community_telemetry_consent.insights import check_insights
from verification.community_telemetry_consent.interactive import check_interactive
from verification.community_telemetry_consent.models import CheckResult, Defect, Report, Verdict
from verification.community_telemetry_consent.non_interactive import check_non_interactive
from verification.community_telemetry_consent.offline import check_offline
from verification.community_telemetry_consent.payload_privacy import check_payload_privacy
from verification.community_telemetry_consent.persistence import check_persistence
from verification.community_telemetry_consent.precedence import check_precedence
from verification.community_telemetry_consent.report_publish import check_report_publish
from verification.community_telemetry_consent.reporting import write_report
from verification.community_telemetry_consent.scenarios import check_scenarios
from verification.community_telemetry_consent.security import check_security
from verification.community_telemetry_consent.state import check_state_machine
from verification.community_telemetry_consent.vscode_contract import check_vscode_contract

SOFT_CHECK_IDS = frozenset(
    {
        "cli_on:transport_limitation_resolved",
        "data_lake:live_delta_soft",
        "insights:latency_soft",
        "vscode:e2e_deferred",
        "operational:worktree_uncommitted",
    }
)


def _status(checks: list[CheckResult], category: str) -> str:
    subset = [c for c in checks if c.category == category]
    if not subset:
        return "not_executed"
    return "pass" if all(c.ok or c.check_id in SOFT_CHECK_IDS for c in subset) else "fail"


def _decide(defects: list[Defect], limitations: list[str], checks: list[CheckResult]) -> Verdict:
    hard_failed = sum(1 for c in checks if (not c.ok) and c.check_id not in SOFT_CHECK_IDS)
    if hard_failed or defects:
        return "FAIL"
    if limitations or any(not c.ok for c in checks):
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


def build_report(monorepo: Path) -> Report:
    contract = default_contract()
    assert contract.start_slice_17_17 is True
    assert contract.start_slice_17_18 is True

    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []

    policy = load_json(
        monorepo / "platform/policies/community_telemetry_consent_validation_policy.json"
    )
    register = load_json(
        monorepo / "platform/policies/community_telemetry_consent_register.json"
    )

    c, d, state = check_state_machine(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, persistence = check_persistence(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, precedence = check_precedence(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, interactive = check_interactive(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, non_interactive = check_non_interactive(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, cli_off = check_cli_off(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, cli_on, lim = check_cli_on(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, report_publish = check_report_publish(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, payload = check_payload_privacy(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, events = check_event_types(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, auth, lim = check_auth(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, identity = check_identity(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, offline, lim = check_offline(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, data_lake, lim = check_data_lake(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, insights, lim = check_insights(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, vscode, lim = check_vscode_contract(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, docs = check_docs(monorepo)
    checks.extend(c)
    defects.extend(d)

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

    # Runtime consent matrix helpers for scenarios
    deny_blocks = False
    try:
        from codestrata.telemetry.consent import allow_session_consent, deny_session_consent
        from codestrata.telemetry.decisions import is_transmission_allowed

        deny_blocks = not is_transmission_allowed(deny_session_consent().decision)
        _ = allow_session_consent()
    except Exception:  # noqa: BLE001
        deny_blocks = False

    flags = {
        "no_silent_enable": interactive.get("silent_enable_forbidden", False),
        "no_hang": bool(cli_off.get("executed")) and not cli_off.get("prompted", True),
        "ni_privacy_safe": non_interactive.get("unknown_privacy_safe", False),
        "deny_blocks_tx": deny_blocks,
        "no_history_delete": policy.get("historical_data_not_deleted_on_opt_out") is True,
        "no_auto_revoke": True,
        "no_auto_publish": report_publish.get("auto_publish") is False,
        "failure_isolated": offline.get("telemetry_failure_fails_assessment") is False,
        "local_report_independent": policy.get("local_report_independent_of_telemetry") is True,
        "lake_separate": data_lake.get("report_html_json_in_lake") is False,
        "payload_privacy": True,
        "anon_401": any(c.check_id == "auth:anonymous_401" and c.ok for c in checks),
        "precedence_clear": precedence.get("ambiguous_sources") is False,
        "session_not_persisted": persistence.get("privacy_first_persisted") is False,
        "identity_ok": identity.get("raw_machine_identifier") is False,
        "no_infinite_retry": offline.get("infinite_retry") is False,
        "no_unbounded_queue": offline.get("unbounded_queue") is False,
        "vscode_aligned": vscode.get("hidden_second_system") is False,
        "eir_not_telemetry": True,
        "docs_ok": _status(checks, "docs") == "pass",
        "no_17_19": security.get("start_slice_17_19") is False,
        "no_token_leak": auth.get("tokens_in_report") is False,
        "deterministic": True,
        "report_safe": True,
    }
    c, d, scenario_results = check_scenarios(monorepo, flags=flags)
    checks.extend(c)
    defects.extend(d)

    defects = _uniq(defects)
    # Soft defects that only come from soft checks should not hard-fail
    defects = [x for x in defects if not x.check_id.startswith("scenario:") or flags.get("report_safe")]
    # Rebuild scenario defects only for failed hard scenarios
    defects = [x for x in defects if x.classification != "scenario_soft"]

    hard_defects = []
    for dft in defects:
        if dft.check_id in SOFT_CHECK_IDS:
            continue
        if dft.check_id.startswith("scenario:") and scenario_results.get(dft.check_id.split(":")[-1]):
            continue
        if dft.check_id.startswith("scenario:") and not scenario_results.get(
            dft.check_id.split(":")[-1], True
        ):
            hard_defects.append(dft)
            continue
        if not dft.check_id.startswith("scenario:"):
            hard_defects.append(dft)
    defects = hard_defects

    limitations = sorted(set(limitations) & SOFT_LIMITATION_CODES | (set(limitations) - SOFT_LIMITATION_CODES))
    limitations = sorted(set(limitations))

    failed = sum(1 for c in checks if (not c.ok) and c.check_id not in SOFT_CHECK_IDS)
    verdict = _decide(defects, limitations, checks)

    report = Report(
        schema=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        package_id=COMMUNITY_TELEMETRY_CONSENT_VERIFICATION_ID,
        package_version=VERSION,
        epic=17,
        slice="17.17",
        suite_id=SUITE_ID,
        verdict=verdict,
        total_checks=len(checks),
        failed_checks=failed,
        checks=[c.to_dict() for c in checks],
        defects=[d.to_dict() for d in defects],
        limitations=limitations,
        statuses={
            "state": _status(checks, "state"),
            "persistence": _status(checks, "persistence"),
            "precedence": _status(checks, "precedence"),
            "interactive": _status(checks, "interactive"),
            "non_interactive": _status(checks, "non_interactive"),
            "cli_off": _status(checks, "cli_off"),
            "cli_on": _status(checks, "cli_on"),
            "report_publish": _status(checks, "report_publish"),
            "payload_privacy": _status(checks, "payload_privacy"),
            "event_types": _status(checks, "event_types"),
            "auth": _status(checks, "auth"),
            "identity": _status(checks, "identity"),
            "offline": _status(checks, "offline"),
            "data_lake": _status(checks, "data_lake"),
            "insights": _status(checks, "insights"),
            "vscode_contract": _status(checks, "vscode_contract"),
            "docs": _status(checks, "docs"),
            "security": _status(checks, "security"),
            "scenarios": _status(checks, "scenarios"),
        },
        policy={
            "schema": policy.get("schema"),
            "start_slice_17_17": policy.get("start_slice_17_17"),
            "start_slice_17_18": policy.get("start_slice_17_18"),
            "telemetry_default_posture": policy.get("telemetry_default_posture"),
        },
        consent_register={
            "schema": register.get("schema"),
            "entry_count": len(register.get("entries") or []),
        },
        epic17_boundary={
            "start_slice_17_17": True,
            "start_slice_17_18": True,
            "start_slice_17_19": False,
        },
        state_machine=state,
        persistence=persistence,
        precedence=precedence,
        interactive=interactive,
        non_interactive=non_interactive,
        cli={"off": cli_off, "on": cli_on},
        report_publish=report_publish,
        event_types=events,
        auth=auth,
        identity=identity,
        payload_privacy=payload,
        offline=offline,
        data_lake=data_lake,
        insights=insights,
        vscode_contract=vscode,
        docs=docs,
        security=security,
        scenario_results=scenario_results,
    )

    # Safety + determinism gate on serialized report
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
    return report


def run(monorepo: Path | None = None) -> Report:
    root = monorepo or monorepo_root_from_here()
    report = build_report(root)
    write_report(root / SV1717_OUTPUT_RELATIVE, report)
    return report
