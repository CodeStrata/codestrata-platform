"""Negative scenario matrix for Slice 17.18 (A–Z)."""

from __future__ import annotations

from pathlib import Path

from verification.community_data_lake_insights.helpers import check
from verification.community_data_lake_insights.models import CheckResult, Defect


def check_scenarios(
    monorepo: Path,
    *,
    flags: dict[str, bool],
) -> tuple[list[CheckResult], list[Defect], dict[str, bool]]:
    scenarios: list[tuple[str, str, bool]] = [
        ("A", "telemetry ON still uses UnavailableTelemetryTransport", flags.get("transport_wired", False)),
        ("B", "live probe skipped again", flags.get("live_probe_completed", False)),
        ("C", "valid authenticated event not persisted", flags.get("events_persisted", False)),
        ("D", "report HTML/JSON enters Data Lake", flags.get("no_reports_in_lake", False)),
        ("E", "source/findings/prompt enters Data Lake", flags.get("payload_privacy", False)),
        ("F", "Data Lake limited to current/previous", flags.get("append_oriented", False)),
        ("G", "report bucket used as Insights source", flags.get("insights_reads_lake", False)),
        ("H", "Insights uses test-only reader in production", flags.get("bounded_reader", False)),
        ("I", "query_budget_reached remains for normal window", flags.get("query_budget_ok", False)),
        ("J", "missing stream crashes dashboard", flags.get("empty_stream_safe", False)),
        ("K", "malformed object crashes all aggregation", flags.get("failure_isolated", False)),
        ("L", "raw installation ID exposed", flags.get("no_installation_id", False)),
        ("M", "S3 object keys exposed", flags.get("no_s3_keys", False)),
        ("N", "dashboard leaks report contents", flags.get("no_report_html", False)),
        ("O", "time window uses local developer timezone incorrectly", flags.get("utc_windows", False)),
        ("P", "duplicate event silently corrupts metric semantics", flags.get("dedupe_ok", False)),
        ("Q", "unauthenticated ingestion succeeds", flags.get("anon_401", False)),
        ("R", "Data Lake becomes public", flags.get("pab_ok", False)),
        ("S", "broad IAM introduced", flags.get("no_broad_iam", False)),
        ("T", "17.13 reports expected/stored in Data Lake", flags.get("no_17_13_reports_in_lake", False)),
        ("U", "full 22-repo release corpus rerun happens early", flags.get("corpus_deferred", False)),
        ("V", "community status website feature starts", flags.get("no_status_api", False)),
        ("W", "Slice 17.20 starts", flags.get("no_17_20", False)),
        ("X", "secret/token leak", flags.get("no_token_leak", False)),
        ("Y", "verifier nondeterministic", flags.get("deterministic", False)),
        ("Z", "report leaks AWS/local internals", flags.get("report_safe", False)),
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
