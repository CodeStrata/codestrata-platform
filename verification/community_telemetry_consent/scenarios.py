"""Negative scenario matrix for Slice 17.17."""

from __future__ import annotations

from pathlib import Path

from verification.community_telemetry_consent.helpers import check
from verification.community_telemetry_consent.models import CheckResult, Defect


def check_scenarios(
    monorepo: Path,
    *,
    flags: dict[str, bool],
) -> tuple[list[CheckResult], list[Defect], dict[str, bool]]:
    scenarios: list[tuple[str, str, bool]] = [
        ("A", "fresh install silently enables telemetry", flags.get("no_silent_enable", False)),
        ("B", "non-interactive run hangs", flags.get("no_hang", False)),
        ("C", "non-interactive UNKNOWN enables telemetry", flags.get("ni_privacy_safe", False)),
        ("D", "opt-out still sends events", flags.get("deny_blocks_tx", False)),
        ("E", "opt-out deletes historical Data Lake events", flags.get("no_history_delete", False)),
        ("F", "opt-out deletes published reports", flags.get("no_auto_revoke", False)),
        ("G", "opt-in automatically publishes report", flags.get("no_auto_publish", False)),
        ("H", "telemetry failure fails assessment", flags.get("failure_isolated", False)),
        ("I", "telemetry failure removes local report", flags.get("local_report_independent", False)),
        ("J", "report HTML/JSON enters Data Lake", flags.get("lake_separate", False)),
        ("K", "source code enters telemetry", flags.get("payload_privacy", False)),
        ("L", "findings/evidence enter telemetry", flags.get("payload_privacy", False)),
        ("M", "prompts/responses enter telemetry", flags.get("payload_privacy", False)),
        ("N", "auth bypass allows anonymous ingestion", flags.get("anon_401", False)),
        ("O", "consent precedence ambiguous", flags.get("precedence_clear", False)),
        ("P", "restart loses persisted consent unexpectedly", flags.get("session_not_persisted", False)),
        ("Q", "re-opt-in duplicates/corrupts identity", flags.get("identity_ok", False)),
        ("R", "infinite retries offline", flags.get("no_infinite_retry", False)),
        ("S", "unbounded local telemetry queue", flags.get("no_unbounded_queue", False)),
        ("T", "VS Code uses separate hidden consent semantics", flags.get("vscode_aligned", False)),
        ("U", "EIR content uploaded via telemetry", flags.get("eir_not_telemetry", False)),
        ("V", "docs claim fields absent when code sends them", flags.get("docs_ok", False)),
        ("W", "Slice 17.19 starts", flags.get("no_17_19", False)),
        ("X", "token/credential leak", flags.get("no_token_leak", False)),
        ("Y", "verifier nondeterministic", flags.get("deterministic", False)),
        ("Z", "verification report leaks IDs/paths/AWS internals", flags.get("report_safe", False)),
    ]
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    results: dict[str, bool] = {}
    for letter, detail, ok in scenarios:
        results[letter] = bool(ok)
        checks.append(check(f"scenario:{letter}", bool(ok), detail, "scenarios"))
        if not ok:
            defects.append(
                Defect(
                    classification=f"scenario_{letter}",
                    check_id=f"scenario:{letter}",
                    expected="pass",
                    detail=detail,
                )
            )
    _ = monorepo
    return checks, defects, results
