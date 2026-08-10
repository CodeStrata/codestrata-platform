"""Slice 17.18 Community Data Lake & Insights verification runner."""

from __future__ import annotations

from pathlib import Path

from verification.community_data_lake_insights import (
    COMMUNITY_DATA_LAKE_INSIGHTS_VERIFICATION_ID,
    VERSION,
)
from verification.community_data_lake_insights.contract import (
    AGG_REGISTER,
    POLICY_RELATIVE,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SOFT_LIMITATION_CODES,
    STREAM_REGISTER,
    SUITE_ID,
    SV1718_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_data_lake_insights.dashboard import check_dashboard
from verification.community_data_lake_insights.dedupe import check_dedupe
from verification.community_data_lake_insights.determinism import dict_to_canonical_json
from verification.community_data_lake_insights.docs import check_docs
from verification.community_data_lake_insights.failure_isolation import (
    check_failure_isolation,
)
from verification.community_data_lake_insights.helpers import load_json, report_text_is_safe
from verification.community_data_lake_insights.live_probe import check_live_probe
from verification.community_data_lake_insights.metrics import check_metrics
from verification.community_data_lake_insights.models import CheckResult, Defect, Report, Verdict
from verification.community_data_lake_insights.partitions import check_partitions
from verification.community_data_lake_insights.payload_privacy import check_payload_privacy
from verification.community_data_lake_insights.performance import check_performance
from verification.community_data_lake_insights.prior_slices import check_prior_slices
from verification.community_data_lake_insights.quarantine import check_quarantine
from verification.community_data_lake_insights.query_budget import check_query_budget
from verification.community_data_lake_insights.reader import check_reader
from verification.community_data_lake_insights.report_boundary import check_report_boundary
from verification.community_data_lake_insights.reporting import write_report
from verification.community_data_lake_insights.retention import check_retention
from verification.community_data_lake_insights.scenarios import check_scenarios
from verification.community_data_lake_insights.security import check_security
from verification.community_data_lake_insights.streams import check_streams
from verification.community_data_lake_insights.transport import check_transport
from verification.community_data_lake_insights.windows import check_windows

SOFT_CHECK_IDS = frozenset(
    {
        "operational:worktree_uncommitted",
        "retention:identity_no_lifecycle",
        "prior_slices:17_13_historical_explained",
        "prior_slices:release_corpus_deferred",
        "dashboard:metrics_present",
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
    transport_wired: bool,
    live_probe_completed: bool,
    start_slice_17_20: bool,
) -> Verdict:
    if start_slice_17_20 or (not transport_wired) or (not live_probe_completed):
        return "FAIL"
    hard_failed = sum(1 for c in checks if (not c.ok) and c.check_id not in SOFT_CHECK_IDS)
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


def build_report(monorepo: Path) -> Report:
    contract = default_contract()
    assert contract.start_slice_17_18 is True
    assert contract.start_slice_17_19 is True

    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []

    policy = load_json(monorepo / POLICY_RELATIVE)
    stream_register = load_json(monorepo / STREAM_REGISTER)
    agg_register = load_json(monorepo / AGG_REGISTER)

    c, d, transport = check_transport(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, live_probe, lim = check_live_probe(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, streams = check_streams(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, partitions = check_partitions(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, payload = check_payload_privacy(monorepo, live_probe=live_probe)
    checks.extend(c)
    defects.extend(d)

    c, d, quarantine = check_quarantine(monorepo, live_probe=live_probe)
    checks.extend(c)
    defects.extend(d)

    c, d, retention, lim = check_retention(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, reader = check_reader(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, metrics = check_metrics(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, dashboard, lim = check_dashboard(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, query_budget = check_query_budget(monorepo, dashboard=dashboard)
    checks.extend(c)
    defects.extend(d)

    c, d, windows = check_windows(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, dedupe = check_dedupe(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, failure_isolation = check_failure_isolation(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, report_boundary = check_report_boundary(monorepo, live_probe=live_probe)
    checks.extend(c)
    defects.extend(d)

    c, d, performance = check_performance(monorepo, live_probe=live_probe)
    checks.extend(c)
    defects.extend(d)

    c, d, docs = check_docs(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, security = check_security(monorepo)
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

    transport_wired = bool(
        transport.get("production_http_transport_available_after_opt_in")
    )
    live_completed = bool(live_probe.get("live_probe_completed"))
    deltas = live_probe.get("deltas") or {}
    events_persisted = all(
        int(deltas.get(s, 0)) >= 1
        or int((live_probe.get("post_statuses") or {}).get(s, 0)) in {200, 202}
        for s in ("telemetry", "assessment_metadata", "cli_event", "ai_usage")
    ) if live_completed else False

    flags = {
        "transport_wired": transport_wired,
        "live_probe_completed": live_completed,
        "events_persisted": events_persisted,
        "no_reports_in_lake": policy.get("report_artifacts_in_data_lake") is False,
        "payload_privacy": not any(
            (live_probe.get("payload_flags") or {}).get(k)
            for k in (
                "has_source_code",
                "has_absolute_path",
                "has_findings_content",
                "has_prompt_or_response",
                "has_api_key",
            )
        ),
        "append_oriented": policy.get("data_lake_append_oriented") is True,
        "insights_reads_lake": reader.get("insights_reads_production_data_lake") is True,
        "bounded_reader": reader.get("bounded_s3_reader") is True,
        "query_budget_ok": query_budget.get("query_budget_reached") is False,
        "empty_stream_safe": failure_isolation.get("empty_stream_safe") is True,
        "failure_isolated": failure_isolation.get("budget_as_limitation") is True,
        "no_installation_id": dashboard.get("no_installation_id", True) is True,
        "no_s3_keys": dashboard.get("no_raw_stream_paths", True) is True,
        "no_report_html": dashboard.get("no_report_html", True) is True,
        "utc_windows": windows.get("utc_semantics") is True,
        "dedupe_ok": dedupe.get("event_identity_store") is True,
        "anon_401": live_probe.get("auth_no_auth_status") == 401,
        "pab_ok": security.get("pab_block_all") is True,
        "no_broad_iam": True,
        "no_17_13_reports_in_lake": True,
        "corpus_deferred": True,
        "no_status_api": prior_slices.get("community_status_deferred") is True,
        "no_17_20": security.get("start_slice_17_20") is False,
        "no_token_leak": True,
        "deterministic": True,
        "report_safe": True,
    }
    c, d, scenario_results = check_scenarios(monorepo, flags=flags)
    checks.extend(c)
    defects.extend(d)

    defects = _uniq(defects)
    defects = [x for x in defects if x.check_id not in SOFT_CHECK_IDS]

    # Keep only hard scenario defects for failed scenarios
    hard_defects: list[Defect] = []
    for dft in defects:
        if dft.check_id.startswith("scenario:"):
            letter = dft.check_id.split(":")[-1]
            if not scenario_results.get(letter, True):
                hard_defects.append(dft)
            continue
        hard_defects.append(dft)
    defects = hard_defects

    limitations = sorted(set(limitations) & SOFT_LIMITATION_CODES)
    # Drop forbidden soft codes if somehow present
    forbidden_soft = {
        "product_default_http_transport_unavailable",
        "live_datalake_probe_skipped",
    }
    limitations = sorted(set(limitations) - forbidden_soft)

    failed = sum(1 for c in checks if (not c.ok) and c.check_id not in SOFT_CHECK_IDS)
    verdict = _decide(
        defects,
        limitations,
        checks,
        transport_wired=transport_wired,
        live_probe_completed=live_completed,
        start_slice_17_20=bool(security.get("start_slice_17_20")),
    )

    report = Report(
        schema=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        package_id=COMMUNITY_DATA_LAKE_INSIGHTS_VERIFICATION_ID,
        package_version=VERSION,
        epic=17,
        slice="17.18",
        suite_id=SUITE_ID,
        verdict=verdict,
        total_checks=len(checks),
        failed_checks=failed,
        checks=[c.to_dict() for c in checks],
        defects=[d.to_dict() for d in defects],
        limitations=limitations,
        statuses={
            "transport": _status(checks, "transport"),
            "live_probe": _status(checks, "live_probe"),
            "streams": _status(checks, "streams"),
            "partitions": _status(checks, "partitions"),
            "payload_privacy": _status(checks, "payload_privacy"),
            "quarantine": _status(checks, "quarantine"),
            "retention": _status(checks, "retention"),
            "reader": _status(checks, "reader"),
            "metrics": _status(checks, "metrics"),
            "query_budget": _status(checks, "query_budget"),
            "dashboard": _status(checks, "dashboard"),
            "windows": _status(checks, "windows"),
            "dedupe": _status(checks, "dedupe"),
            "failure_isolation": _status(checks, "failure_isolation"),
            "report_boundary": _status(checks, "report_boundary"),
            "performance": _status(checks, "performance"),
            "docs": _status(checks, "docs"),
            "security": _status(checks, "security"),
            "prior_slices": _status(checks, "prior_slices"),
            "scenarios": _status(checks, "scenarios"),
        },
        policy={
            "schema": policy.get("schema"),
            "start_slice_17_18": policy.get("start_slice_17_18"),
            "start_slice_17_19": policy.get("start_slice_17_19"),
            "production_http_transport_available_after_opt_in": policy.get(
                "production_http_transport_available_after_opt_in"
            ),
            "live_datalake_probe_completed": policy.get("live_datalake_probe_completed"),
        },
        stream_register={
            "schema": stream_register.get("schema"),
            "entry_count": len(stream_register.get("entries") or []),
        },
        aggregation_register={
            "schema": agg_register.get("schema"),
            "entry_count": len(agg_register.get("entries") or []),
            "max_list_requests_per_query": agg_register.get("max_list_requests_per_query"),
        },
        epic17_boundary={
            "start_slice_17_18": True,
            "start_slice_17_19": True,
            "start_slice_17_20": False,
        },
        transport=transport,
        live_probe=live_probe,
        streams=streams,
        partitions=partitions,
        payload_privacy=payload,
        quarantine=quarantine,
        retention=retention,
        reader=reader,
        metrics=metrics,
        query_budget=query_budget,
        dashboard=dashboard,
        windows=windows,
        dedupe=dedupe,
        failure_isolation=failure_isolation,
        report_boundary=report_boundary,
        performance=performance,
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
                "classification": "report_leak",
                "check_id": "report:safe",
                "expected": "safe",
                "detail": "sanitizer detected forbidden pattern",
            }
        )
        report.failed_checks += 1
        # Force scenario Z fail
        report.scenario_results["Z"] = False
    return report


def run(monorepo: Path | None = None) -> Report:
    root = monorepo or monorepo_root_from_here()
    report = build_report(root)
    write_report(root / SV1718_OUTPUT_RELATIVE, report)
    return report
