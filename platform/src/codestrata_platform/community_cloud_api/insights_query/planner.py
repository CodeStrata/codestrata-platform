"""Pure deterministic S3 prefix planner for Insights queries (Slice 15.5).

No AWS SDK imports, no network, no credentials, no installation IDs.
"""

from __future__ import annotations

from datetime import date, timedelta

from codestrata_platform.community_cloud_api.insights_query.errors import (
    InsightsQueryPlanError,
)
from codestrata_platform.community_cloud_api.insights_query.models import (
    DateWindow,
    QueryBudgets,
    QueryPlan,
)
from codestrata_platform.community_cloud_api.insights_query.policy import (
    ALLOWED_STREAMS,
    EXTERNAL_METRICS,
    LIFETIME_METRICS,
    MAX_DATE_SPAN_DAYS_DEFAULT,
    MAX_DATE_SPAN_DAYS_LIFETIME,
    METRIC_STREAMS,
    SUPPORTED_SCHEMA_VERSIONS,
    default_query_budgets,
)


def _iter_days(start: date, end: date) -> list[date]:
    days: list[date] = []
    cur = start
    while cur <= end:
        days.append(cur)
        cur += timedelta(days=1)
    return days


def _day_prefix(stream: str, schema_version: str, day: date) -> str:
    return (
        f"raw/stream={stream}/schema_version={schema_version}/"
        f"year={day.year:04d}/month={day.month:02d}/day={day.day:02d}/"
    )


def _validate_streams(streams: tuple[str, ...]) -> None:
    if not streams:
        raise InsightsQueryPlanError("unsupported_stream", "empty")
    for stream in streams:
        if stream not in ALLOWED_STREAMS:
            raise InsightsQueryPlanError("unsupported_stream", stream)
        if stream.startswith("quarantine") or "quarantine" in stream:
            raise InsightsQueryPlanError("unsupported_stream", "quarantine")


def _validate_schema_versions(versions: tuple[str, ...]) -> None:
    if not versions:
        raise InsightsQueryPlanError("unsupported_schema_version", "empty")
    for ver in versions:
        if ver not in SUPPORTED_SCHEMA_VERSIONS:
            raise InsightsQueryPlanError("unsupported_schema_version", ver)


def _validate_window(window: DateWindow, *, max_span_days: int) -> None:
    span = (window.end_date - window.start_date).days + 1
    if span < 1:
        raise InsightsQueryPlanError("invalid_query_window", "empty")
    if span > max_span_days:
        raise InsightsQueryPlanError("invalid_query_window", "span_exceeded")


def reject_caller_prefix(prefix: str) -> None:
    """Dashboard/API must never accept caller-supplied S3 prefixes."""

    raise InsightsQueryPlanError("invalid_query_window", "caller_prefix_forbidden")


def plan_prefixes(
    *,
    streams: tuple[str, ...],
    schema_versions: tuple[str, ...] = ("1.0",),
    window: DateWindow,
    budgets: QueryBudgets | None = None,
    max_span_days: int | None = None,
    metric: str | None = None,
) -> QueryPlan:
    """Build a bounded list of day prefixes for approved streams/versions."""

    if any(s == "quarantine" or s.startswith("quarantine/") for s in streams):
        raise InsightsQueryPlanError("unsupported_stream", "quarantine")
    _validate_streams(streams)
    _validate_schema_versions(schema_versions)

    span_limit = max_span_days
    if span_limit is None:
        span_limit = (
            MAX_DATE_SPAN_DAYS_LIFETIME
            if metric in LIFETIME_METRICS
            else MAX_DATE_SPAN_DAYS_DEFAULT
        )
    _validate_window(window, max_span_days=span_limit)

    active_budgets = budgets or default_query_budgets()
    days = _iter_days(window.start_date, window.end_date)
    prefixes: list[str] = []
    for stream in streams:
        for ver in schema_versions:
            for day in days:
                prefixes.append(_day_prefix(stream, ver, day))

    # Deterministic order.
    ordered = tuple(sorted(set(prefixes)))
    # Reject any accidental root / quarantine shapes.
    for prefix in ordered:
        if prefix == "raw/" or prefix.startswith("quarantine/"):
            raise InsightsQueryPlanError("invalid_query_window", "unsafe_prefix")
        if ".." in prefix or "*" in prefix:
            raise InsightsQueryPlanError("invalid_query_window", "unsafe_prefix")
        for forbidden in (
            "installation_id=",
            "provider_family=",
            "model_family=",
            "primary_language=",
            "package_ecosystem=",
        ):
            if forbidden in prefix:
                raise InsightsQueryPlanError("invalid_query_window", "privacy_dimension")

    return QueryPlan(
        streams=tuple(streams),
        schema_versions=tuple(schema_versions),
        prefixes=ordered,
        start_date=window.start_date.isoformat(),
        end_date=window.end_date.isoformat(),
        budgets=active_budgets,
        quarantine_excluded=True,
        completeness_default="complete",
        metric=metric,
    )


def _plan_streams_for_window(
    *,
    streams: tuple[str, ...],
    window: DateWindow,
    budgets: QueryBudgets | None,
    metric: str | None,
    max_span_days: int,
) -> QueryPlan:
    """Plan day prefixes with per-stream schema versions (amd → 1.0+1.1)."""

    _validate_window(window, max_span_days=max_span_days)
    _validate_streams(streams)
    active_budgets = budgets or default_query_budgets()
    days = _iter_days(window.start_date, window.end_date)
    prefixes: list[str] = []
    used_versions: set[str] = set()
    for stream in streams:
        versions = (
            tuple(sorted(SUPPORTED_SCHEMA_VERSIONS))
            if stream == "assessment_metadata"
            else ("1.0",)
        )
        _validate_schema_versions(versions)
        used_versions.update(versions)
        for ver in versions:
            for day in days:
                prefixes.append(_day_prefix(stream, ver, day))
    ordered = tuple(sorted(set(prefixes)))
    return QueryPlan(
        streams=tuple(streams),
        schema_versions=tuple(sorted(used_versions)),
        prefixes=ordered,
        start_date=window.start_date.isoformat(),
        end_date=window.end_date.isoformat(),
        budgets=active_budgets,
        quarantine_excluded=True,
        completeness_default="complete",
        metric=metric,
    )


def plan_metric_query(
    *,
    metric: str,
    window: DateWindow,
    schema_versions: tuple[str, ...] | None = None,
    budgets: QueryBudgets | None = None,
) -> QueryPlan:
    """Plan prefixes for a known Insights metric family.

    When ``schema_versions`` is omitted, each stream uses the versions it
    actually stores: ``assessment_metadata`` plans ``1.0`` and ``1.1``;
    every other stream remains ``1.0`` only.
    """

    if metric in EXTERNAL_METRICS:
        raise InsightsQueryPlanError(
            "unsupported_stream", "external_metric_source_no_s3"
        )
    streams = METRIC_STREAMS.get(metric)
    if streams is None:
        raise InsightsQueryPlanError("unsupported_stream", "unknown_metric")
    if schema_versions is not None:
        return plan_prefixes(
            streams=streams,
            schema_versions=schema_versions,
            window=window,
            budgets=budgets,
            metric=metric,
        )

    span_limit = (
        MAX_DATE_SPAN_DAYS_LIFETIME
        if metric in LIFETIME_METRICS
        else MAX_DATE_SPAN_DAYS_DEFAULT
    )
    return _plan_streams_for_window(
        streams=streams,
        window=window,
        budgets=budgets,
        metric=metric,
        max_span_days=span_limit,
    )


def plan_overview_lake_query(
    *,
    window: DateWindow,
    lake_metrics: tuple[str, ...],
    budgets: QueryBudgets | None = None,
) -> QueryPlan:
    """Single bounded plan covering all lake overview metrics (no duplicate scans).

    Unions METRIC_STREAMS for the requested lake metrics and applies the same
    per-stream schema rules as ``plan_metric_query`` (amd → 1.0 + 1.1).
    """

    streams_set: set[str] = set()
    needs_lifetime_span = False
    for metric in lake_metrics:
        if metric in EXTERNAL_METRICS:
            continue
        mapped = METRIC_STREAMS.get(metric)
        if mapped is None:
            raise InsightsQueryPlanError("unsupported_stream", "unknown_metric")
        streams_set.update(mapped)
        if metric in LIFETIME_METRICS:
            needs_lifetime_span = True
    if not streams_set:
        raise InsightsQueryPlanError("unsupported_stream", "empty")
    # Stable stream order for deterministic plans.
    streams = tuple(sorted(streams_set))
    span_limit = (
        MAX_DATE_SPAN_DAYS_LIFETIME
        if needs_lifetime_span
        else MAX_DATE_SPAN_DAYS_DEFAULT
    )
    return _plan_streams_for_window(
        streams=streams,
        window=window,
        budgets=budgets,
        metric="overview_lake_batch",
        max_span_days=span_limit,
    )
