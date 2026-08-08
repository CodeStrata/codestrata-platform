"""Metric aggregators — pure functions over normalized events."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from typing import Any, Callable

from codestrata_platform.community_cloud_api.insights.completeness import (
    finalize_limitations,
    resolve_completeness,
)
from codestrata_platform.community_cloud_api.insights.models import (
    AggregationContext,
    MetricGroup,
    MetricResult,
    MetricWindow,
)
from codestrata_platform.community_cloud_api.insights.policy import (
    CANCELLED_RESULTS,
    CANCELLED_STATUSES,
    CHECKPOINT_MODE,
    FAILED_RESULTS,
    FAILED_STATUSES,
    METRIC_HORIZONS,
    PROVIDER_UNAVAILABLE,
    SUCCESS_RESULTS,
    SUCCESS_STATUSES,
)
from codestrata_platform.community_cloud_api.insights.suppression import share, suppress_groups


def _window(metric_id: str, start: date, end: date) -> MetricWindow:
    return MetricWindow(
        start_date_utc=start,
        end_date_utc=end,
        horizon=METRIC_HORIZONS.get(metric_id, "bounded_period"),
    )


def _base_limitations(ctx: AggregationContext) -> list[str]:
    lim: list[str] = [
        "production_ingestion_still_unwired",
        "no_live_dashboard_data_claim",
    ]
    if ctx.diagnostics.budget_reached:
        lim.append("query_budget_reached")
    if ctx.diagnostics.malformed_objects or ctx.diagnostics.unsupported_schema_objects:
        lim.append("malformed_objects_omitted")
    if ctx.missing_installation_id_count:
        lim.append("optional_identity_undercount")
    return lim


def _event_sort_key(event: dict[str, Any]) -> tuple[str, str]:
    occurred = event.get("occurred_at") or ""
    eid = event.get("event_id") or ""
    return (str(occurred), str(eid))


def aggregate_total_installations(
    ctx: AggregationContext, start: date, end: date
) -> MetricResult:
    ids: set[str] = set()
    missing = 0
    for ev in ctx.events:
        iid = ev.get("installation_id")
        if iid:
            ids.add(iid)
        else:
            missing += 1
    ctx.missing_installation_id_count = max(ctx.missing_installation_id_count, missing)
    lim = _base_limitations(ctx)
    lim.append("retention_window_limited")
    completeness = resolve_completeness(
        diagnostics=ctx.diagnostics,
        missing_identity=missing > 0,
    )
    return MetricResult(
        metric_id="total_anonymous_installations",
        status="ok",
        window=_window("total_anonymous_installations", start, end),
        value=len(ids),
        completeness=completeness,
        limitations=finalize_limitations(lim),
    )


def aggregate_daily_active(
    ctx: AggregationContext, start: date, end: date
) -> MetricResult:
    # Single UTC day preferred; if multi-day window, count distinct IDs across window days
    # but primary semantics are one day — use end_date as the day when start==end.
    ids: set[str] = set()
    missing = 0
    for ev in ctx.events:
        if not _is_approved_activity(ev):
            continue
        iid = ev.get("installation_id")
        if iid:
            ids.add(iid)
        else:
            missing += 1
    ctx.missing_installation_id_count = max(ctx.missing_installation_id_count, missing)
    lim = _base_limitations(ctx)
    completeness = resolve_completeness(
        diagnostics=ctx.diagnostics, missing_identity=missing > 0
    )
    return MetricResult(
        metric_id="daily_active_installations",
        status="ok",
        window=_window("daily_active_installations", start, end),
        value=len(ids),
        completeness=completeness,
        limitations=finalize_limitations(lim),
    )


def aggregate_monthly_active(
    ctx: AggregationContext, start: date, end: date
) -> MetricResult:
    # Rolling 30 UTC days ending at end_date.
    window_start = end - timedelta(days=29)
    effective_start = max(start, window_start)
    ids: set[str] = set()
    missing = 0
    for ev in ctx.events:
        if not _is_approved_activity(ev):
            continue
        pd = ev.get("partition_date")
        if isinstance(pd, str):
            try:
                d = date.fromisoformat(pd)
            except ValueError:
                d = None
            if d is not None and (d < effective_start or d > end):
                continue
        iid = ev.get("installation_id")
        if iid:
            ids.add(iid)
        else:
            missing += 1
    ctx.missing_installation_id_count = max(ctx.missing_installation_id_count, missing)
    lim = _base_limitations(ctx)
    completeness = resolve_completeness(
        diagnostics=ctx.diagnostics, missing_identity=missing > 0
    )
    return MetricResult(
        metric_id="monthly_active_installations",
        status="ok",
        window=MetricWindow(
            start_date_utc=effective_start,
            end_date_utc=end,
            horizon="rolling_30_day",
        ),
        value=len(ids),
        completeness=completeness,
        limitations=finalize_limitations(lim),
    )


def aggregate_first_assessments(
    ctx: AggregationContext, start: date, end: date
) -> MetricResult:
    by_install: dict[str, dict[str, Any]] = {}
    missing = 0
    for ev in sorted(
        (e for e in ctx.events if e.get("stream") == "assessment_metadata"),
        key=_event_sort_key,
    ):
        if _is_cancelled(ev):
            continue
        iid = ev.get("installation_id")
        if not iid:
            missing += 1
            continue
        if iid not in by_install:
            by_install[iid] = ev
    ctx.missing_installation_id_count = max(ctx.missing_installation_id_count, missing)
    lim = _base_limitations(ctx)
    lim.append("retention_window_limited")
    if CHECKPOINT_MODE == "retention_only_with_limitation":
        lim.append("first_repeat_retention_only")
    completeness = resolve_completeness(
        diagnostics=ctx.diagnostics, missing_identity=missing > 0
    )
    return MetricResult(
        metric_id="first_assessments",
        status="ok",
        window=_window("first_assessments", start, end),
        value=len(by_install),
        completeness=completeness,
        limitations=finalize_limitations(lim),
    )


def aggregate_repeat_assessments(
    ctx: AggregationContext, start: date, end: date
) -> MetricResult:
    by_install: dict[str, list[dict[str, Any]]] = defaultdict(list)
    missing = 0
    for ev in sorted(
        (e for e in ctx.events if e.get("stream") == "assessment_metadata"),
        key=_event_sort_key,
    ):
        if _is_cancelled(ev):
            continue
        iid = ev.get("installation_id")
        if not iid:
            missing += 1
            continue
        by_install[iid].append(ev)
    repeat_events = 0
    for events in by_install.values():
        if len(events) > 1:
            repeat_events += len(events) - 1
    ctx.missing_installation_id_count = max(ctx.missing_installation_id_count, missing)
    lim = _base_limitations(ctx)
    lim.append("retention_window_limited")
    lim.append("first_repeat_retention_only")
    completeness = resolve_completeness(
        diagnostics=ctx.diagnostics, missing_identity=missing > 0
    )
    return MetricResult(
        metric_id="repeat_assessments",
        status="ok",
        window=_window("repeat_assessments", start, end),
        value=repeat_events,
        completeness=completeness,
        limitations=finalize_limitations(lim),
    )


def aggregate_successful(ctx: AggregationContext, start: date, end: date) -> MetricResult:
    count = 0
    for ev in ctx.events:
        if ev.get("stream") != "assessment_metadata":
            continue
        if _is_cancelled(ev):
            continue
        if _is_success(ev):
            count += 1
    lim = _base_limitations(ctx)
    completeness = resolve_completeness(
        diagnostics=ctx.diagnostics, missing_identity=False
    )
    return MetricResult(
        metric_id="successful_assessments",
        status="ok",
        window=_window("successful_assessments", start, end),
        value=count,
        completeness=completeness,
        limitations=finalize_limitations(lim),
    )


def aggregate_failed(ctx: AggregationContext, start: date, end: date) -> MetricResult:
    count = 0
    for ev in ctx.events:
        if ev.get("stream") != "assessment_metadata":
            continue
        if _is_cancelled(ev):
            continue
        if _is_failed(ev):
            count += 1
    lim = _base_limitations(ctx)
    completeness = resolve_completeness(
        diagnostics=ctx.diagnostics, missing_identity=False
    )
    return MetricResult(
        metric_id="failed_assessments",
        status="ok",
        window=_window("failed_assessments", start, end),
        value=count,
        completeness=completeness,
        limitations=finalize_limitations(lim),
    )


def aggregate_cli_versions(ctx: AggregationContext, start: date, end: date) -> MetricResult:
    per_version: dict[str, set[str]] = defaultdict(set)
    missing = 0
    for ev in ctx.events:
        if ev.get("stream") != "cli_event":
            continue
        version = ev.get("client_version") or "unknown"
        # Bound: reject empty / overly long arbitrary strings
        if not isinstance(version, str) or len(version) > 32:
            version = "unknown"
        iid = ev.get("installation_id")
        if not iid:
            missing += 1
            continue
        per_version[version].add(iid)
    counts = {k: len(v) for k, v in per_version.items()}
    groups, suppressed = suppress_groups(counts, dimension="client_version")
    denominator = sum(g.count for g in groups)
    lim = _base_limitations(ctx)
    if suppressed:
        lim.append("suppressed_small_groups")
    ctx.missing_installation_id_count = max(ctx.missing_installation_id_count, missing)
    completeness = resolve_completeness(
        diagnostics=ctx.diagnostics, missing_identity=missing > 0
    )
    return MetricResult(
        metric_id="cli_version_adoption",
        status="ok",
        window=_window("cli_version_adoption", start, end),
        value=denominator,
        groups=groups,
        denominator=denominator,
        completeness=completeness,
        limitations=finalize_limitations(lim),
    )


def aggregate_heads(ctx: AggregationContext, start: date, end: date) -> MetricResult:
    head_counts: dict[str, int] = defaultdict(int)
    completed = 0
    for ev in ctx.events:
        if ev.get("stream") != "assessment_metadata":
            continue
        if not _is_success(ev):
            continue
        completed += 1
        for head in ev.get("executed_heads") or []:
            head_counts[head] += 1
    groups, suppressed = suppress_groups(dict(head_counts), dimension="assessment_head")
    # Recompute shares against completed assessments denominator where useful
    denom = completed
    rebuilt: list[MetricGroup] = []
    for g in groups:
        rebuilt.append(
            MetricGroup(
                dimension=g.dimension,
                key=g.key,
                count=g.count,
                share=share(g.count, denom) if denom else None,
                suppressed=g.suppressed,
            )
        )
    lim = _base_limitations(ctx)
    if suppressed:
        lim.append("suppressed_small_groups")
    completeness = resolve_completeness(
        diagnostics=ctx.diagnostics, missing_identity=False
    )
    return MetricResult(
        metric_id="assessment_head_usage",
        status="ok",
        window=_window("assessment_head_usage", start, end),
        value=completed,
        groups=tuple(rebuilt),
        denominator=denom,
        completeness=completeness,
        limitations=finalize_limitations(lim),
    )


def aggregate_language_ecosystem(
    ctx: AggregationContext, start: date, end: date
) -> MetricResult:
    lang_counts: dict[str, int] = defaultdict(int)
    eco_counts: dict[str, int] = defaultdict(int)
    total = 0
    for ev in ctx.events:
        if ev.get("stream") != "assessment_metadata":
            continue
        total += 1
        lang_counts[ev.get("primary_language") or "unknown"] += 1
        eco = ev.get("package_ecosystem")
        if eco:
            eco_counts[eco] += 1
    lang_groups, s1 = suppress_groups(dict(lang_counts), dimension="primary_language")
    eco_groups, s2 = suppress_groups(dict(eco_counts), dimension="package_ecosystem")
    lim = _base_limitations(ctx)
    if s1 or s2:
        lim.append("suppressed_small_groups")
    completeness = resolve_completeness(
        diagnostics=ctx.diagnostics, missing_identity=False
    )
    return MetricResult(
        metric_id="language_ecosystem_distribution",
        status="ok",
        window=_window("language_ecosystem_distribution", start, end),
        value=total,
        groups=lang_groups + eco_groups,
        denominator=total,
        completeness=completeness,
        limitations=finalize_limitations(lim),
    )


def aggregate_providers(ctx: AggregationContext, start: date, end: date) -> MetricResult:
    counts: dict[str, int] = defaultdict(int)
    unavailable = 0
    for ev in ctx.events:
        if ev.get("stream") != "ai_usage":
            continue
        provider = ev.get("provider_family")
        if provider == PROVIDER_UNAVAILABLE:
            unavailable += 1
            continue
        if provider:
            counts[provider] += 1
    groups, suppressed = suppress_groups(dict(counts), dimension="provider_family")
    denom = sum(g.count for g in groups)
    lim = _base_limitations(ctx)
    if suppressed:
        lim.append("suppressed_small_groups")
    completeness = resolve_completeness(
        diagnostics=ctx.diagnostics, missing_identity=False
    )
    return MetricResult(
        metric_id="ai_provider_adoption",
        status="ok",
        window=_window("ai_provider_adoption", start, end),
        value=denom,
        groups=groups,
        denominator=denom,
        completeness=completeness,
        limitations=finalize_limitations(lim),
    )


def aggregate_model_families(
    ctx: AggregationContext, start: date, end: date
) -> MetricResult:
    counts: dict[str, int] = defaultdict(int)
    for ev in ctx.events:
        if ev.get("stream") != "ai_usage":
            continue
        family = ev.get("model_family")
        if family:
            counts[family] += 1
    groups, suppressed = suppress_groups(dict(counts), dimension="model_family")
    denom = sum(g.count for g in groups)
    lim = _base_limitations(ctx)
    if suppressed:
        lim.append("suppressed_small_groups")
    completeness = resolve_completeness(
        diagnostics=ctx.diagnostics, missing_identity=False
    )
    return MetricResult(
        metric_id="ai_model_adoption",
        status="ok",
        window=_window("ai_model_adoption", start, end),
        value=denom,
        groups=groups,
        denominator=denom,
        completeness=completeness,
        limitations=finalize_limitations(lim),
    )


def aggregate_vscode(ctx: AggregationContext, start: date, end: date) -> MetricResult:
    ids: set[str] = set()
    missing = 0
    for ev in ctx.events:
        if ev.get("stream") != "extension_event":
            continue
        if ev.get("operation") not in {"assess", "assess_with_ai"}:
            continue
        iid = ev.get("installation_id")
        if iid:
            ids.add(iid)
        else:
            missing += 1
    ctx.missing_installation_id_count = max(ctx.missing_installation_id_count, missing)
    lim = _base_limitations(ctx)
    completeness = resolve_completeness(
        diagnostics=ctx.diagnostics, missing_identity=missing > 0
    )
    return MetricResult(
        metric_id="vscode_extension_usage",
        status="ok",
        window=_window("vscode_extension_usage", start, end),
        value=len(ids),
        completeness=completeness,
        limitations=finalize_limitations(lim),
    )


def aggregate_release(ctx: AggregationContext, start: date, end: date) -> MetricResult:
    cli: dict[str, set[str]] = defaultdict(set)
    vscode: dict[str, set[str]] = defaultdict(set)
    missing = 0
    for ev in ctx.events:
        stream = ev.get("stream")
        version = ev.get("client_version") or "unknown"
        if not isinstance(version, str) or len(version) > 32:
            version = "unknown"
        iid = ev.get("installation_id")
        if stream == "cli_event":
            if iid:
                cli[version].add(iid)
            else:
                missing += 1
        elif stream == "extension_event":
            if iid:
                vscode[version].add(iid)
            else:
                missing += 1
    cli_groups, s1 = suppress_groups(
        {k: len(v) for k, v in cli.items()}, dimension="cli_client_version"
    )
    vs_groups, s2 = suppress_groups(
        {k: len(v) for k, v in vscode.items()}, dimension="vscode_client_version"
    )
    lim = _base_limitations(ctx)
    if s1 or s2:
        lim.append("suppressed_small_groups")
    ctx.missing_installation_id_count = max(ctx.missing_installation_id_count, missing)
    completeness = resolve_completeness(
        diagnostics=ctx.diagnostics, missing_identity=missing > 0
    )
    total = sum(g.count for g in cli_groups) + sum(g.count for g in vs_groups)
    return MetricResult(
        metric_id="release_adoption",
        status="ok",
        window=_window("release_adoption", start, end),
        value=total,
        groups=cli_groups + vs_groups,
        denominator=total,
        completeness=completeness,
        limitations=finalize_limitations(lim),
    )


def _is_approved_activity(ev: dict[str, Any]) -> bool:
    stream = ev.get("stream")
    if stream == "assessment_metadata":
        return True
    if stream == "telemetry":
        return ev.get("event_type") in {
            "feature_invoked",
            "feature_completed",
            "application_started",
            "application_completed",
            "operation_failed",
        }
    if stream in {"cli_event", "extension_event"}:
        return ev.get("operation") in {"assess", "assess_with_ai"}
    if stream == "ai_usage":
        return True
    return False


def _is_cancelled(ev: dict[str, Any]) -> bool:
    return (
        ev.get("assessment_status") in CANCELLED_STATUSES
        or ev.get("execution_result") in CANCELLED_RESULTS
    )


def _is_success(ev: dict[str, Any]) -> bool:
    return (
        ev.get("assessment_status") in SUCCESS_STATUSES
        or ev.get("execution_result") in SUCCESS_RESULTS
    )


def _is_failed(ev: dict[str, Any]) -> bool:
    if _is_cancelled(ev):
        return False
    return (
        ev.get("assessment_status") in FAILED_STATUSES
        or ev.get("execution_result") in FAILED_RESULTS
    )


Aggregator = Callable[[AggregationContext, date, date], MetricResult]

AGGREGATORS: dict[str, Aggregator] = {
    "total_anonymous_installations": aggregate_total_installations,
    "daily_active_installations": aggregate_daily_active,
    "monthly_active_installations": aggregate_monthly_active,
    "first_assessments": aggregate_first_assessments,
    "repeat_assessments": aggregate_repeat_assessments,
    "successful_assessments": aggregate_successful,
    "failed_assessments": aggregate_failed,
    "cli_version_adoption": aggregate_cli_versions,
    "assessment_head_usage": aggregate_heads,
    "language_ecosystem_distribution": aggregate_language_ecosystem,
    "ai_provider_adoption": aggregate_providers,
    "ai_model_adoption": aggregate_model_families,
    "vscode_extension_usage": aggregate_vscode,
    "release_adoption": aggregate_release,
}
