"""On-demand Insights aggregation service."""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date

from codestrata_platform.community_cloud_api.insights.aggregators import AGGREGATORS
from codestrata_platform.community_cloud_api.insights.completeness import finalize_limitations
from codestrata_platform.community_cloud_api.insights.decoding import (
    decode_object_bytes,
    normalize_event,
)
from codestrata_platform.community_cloud_api.insights.errors import (
    INVALID_METRIC,
    INVALID_WINDOW,
    QUERY_LIMIT_EXCEEDED,
    InsightsAggregationError,
)
from codestrata_platform.community_cloud_api.insights.models import (
    AggregationContext,
    MetricRequest,
    MetricResult,
    MetricWindow,
    OverviewRequest,
)
from codestrata_platform.community_cloud_api.insights.policy import (
    DEFAULT_OVERVIEW_METRICS,
    SUPPORTED_METRICS,
)
from codestrata_platform.community_cloud_api.insights.registry import (
    get_aggregator,
    is_external_metric,
)
from codestrata_platform.community_cloud_api.insights.external_metrics import (
    aggregate_community_sentiment,
    aggregate_github_forks,
    aggregate_github_stars,
    aggregate_published_reports,
)
from codestrata_platform.community_cloud_api.insights.validation_dataset import (
    ValidationCatalogPort,
    aggregate_validation_dataset,
)
from codestrata_platform.community_cloud_api.insights_query.errors import InsightsQueryPlanError
from codestrata_platform.community_cloud_api.insights_query.models import DateWindow, QueryPlan
from codestrata_platform.community_cloud_api.insights_query.planner import (
    plan_metric_query,
    plan_overview_lake_query,
)
from codestrata_platform.community_cloud_api.insights_query.policy import EXTERNAL_METRICS
from codestrata_platform.community_cloud_api.insights_storage.reader import (
    BoundedS3Reader,
    ReaderResult,
)

_LOG = logging.getLogger(__name__)


class InsightsAggregationService:
    def __init__(
        self,
        *,
        reader: BoundedS3Reader | None = None,
        validation_catalog: ValidationCatalogPort | None = None,
        published_reports_port: object | None = None,
        community_sentiment_port: object | None = None,
    ) -> None:
        self._reader = reader
        self._validation_catalog = validation_catalog
        self._published_reports_port = published_reports_port
        self._community_sentiment_port = community_sentiment_port

    def aggregate_metric(self, request: MetricRequest) -> MetricResult:
        return aggregate_metric(
            request,
            reader=self._reader,
            validation_catalog=self._validation_catalog,
            published_reports_port=self._published_reports_port,
            community_sentiment_port=self._community_sentiment_port,
        )

    def aggregate_dashboard_overview(
        self, request: OverviewRequest
    ) -> tuple[MetricResult, ...]:
        return aggregate_dashboard_overview(
            request,
            reader=self._reader,
            validation_catalog=self._validation_catalog,
            published_reports_port=self._published_reports_port,
            community_sentiment_port=self._community_sentiment_port,
        )


def aggregate_metric(
    request: MetricRequest,
    *,
    reader: BoundedS3Reader | None = None,
    validation_catalog: ValidationCatalogPort | None = None,
    published_reports_port: object | None = None,
    community_sentiment_port: object | None = None,
    preloaded: AggregationContext | None = None,
) -> MetricResult:
    metric_id = request.metric_id
    if metric_id not in SUPPORTED_METRICS:
        raise InsightsAggregationError(INVALID_METRIC, "unknown")
    if request.end_date_utc < request.start_date_utc:
        raise InsightsAggregationError(INVALID_WINDOW, "end_before_start")

    if metric_id in EXTERNAL_METRICS or is_external_metric(metric_id):
        if metric_id == "validation_dataset_growth":
            if validation_catalog is None:
                return MetricResult(
                    metric_id=metric_id,
                    status="error",
                    window=MetricWindow(
                        request.start_date_utc, request.end_date_utc, "external"
                    ),
                    value=None,
                    completeness="unavailable",
                    limitations=finalize_limitations(
                        ["source_unavailable", "validation_growth_snapshots_unavailable"]
                    ),
                )
            return aggregate_validation_dataset(
                validation_catalog,
                start=request.start_date_utc,
                end=request.end_date_utc,
            )
        if metric_id == "github_stars":
            return aggregate_github_stars(request.start_date_utc, request.end_date_utc)
        if metric_id == "github_forks":
            return aggregate_github_forks(request.start_date_utc, request.end_date_utc)
        if metric_id == "published_reports":
            return aggregate_published_reports(
                request.start_date_utc,
                request.end_date_utc,
                port=published_reports_port,  # type: ignore[arg-type]
            )
        if metric_id == "community_sentiment":
            return aggregate_community_sentiment(
                request.start_date_utc,
                request.end_date_utc,
                port=community_sentiment_port,  # type: ignore[arg-type]
            )
        return MetricResult(
            metric_id=metric_id,
            status="error",
            window=MetricWindow(
                request.start_date_utc, request.end_date_utc, "external"
            ),
            value=None,
            completeness="unavailable",
            limitations=finalize_limitations(["source_unavailable"]),
        )

    try:
        ctx = preloaded or _load_context(
            metric_id=metric_id,
            start=request.start_date_utc,
            end=request.end_date_utc,
            reader=reader,
        )
    except InsightsAggregationError as exc:
        return _error_result(metric_id, request, exc)

    aggregator = get_aggregator(metric_id)
    return aggregator(ctx, request.start_date_utc, request.end_date_utc)


def aggregate_dashboard_overview(
    request: OverviewRequest,
    *,
    reader: BoundedS3Reader | None = None,
    validation_catalog: ValidationCatalogPort | None = None,
    published_reports_port: object | None = None,
    community_sentiment_port: object | None = None,
) -> tuple[MetricResult, ...]:
    """Overview: one lake read for all S3 metrics; independent external cards.

    Lake metrics (total/first/repeat/successful/failed) share a single
    ``plan_overview_lake_query`` + ``BoundedS3Reader.read_plan`` so telemetry
    objects are not listed/gotten twice. External metrics stay isolated so a
    slow/failed GitHub or registry call cannot rewrite lake results.
    Lake and external work run concurrently so wall time is roughly
    ``max(lake, external)`` rather than the sum.
    """

    metric_ids = request.metric_ids or DEFAULT_OVERVIEW_METRICS
    t0 = time.perf_counter()
    stage_ms: dict[str, float] = {}

    lake_ids = tuple(
        mid
        for mid in metric_ids
        if mid in SUPPORTED_METRICS
        and mid not in EXTERNAL_METRICS
        and not is_external_metric(mid)
    )
    external_ids = tuple(
        mid
        for mid in metric_ids
        if mid in SUPPORTED_METRICS
        and (mid in EXTERNAL_METRICS or is_external_metric(mid))
    )

    lake_ctx: AggregationContext | None = None
    lake_error: InsightsAggregationError | None = None
    external_results: dict[str, MetricResult] = {}

    def _lake_work() -> tuple[
        AggregationContext | None, InsightsAggregationError | None, dict[str, float]
    ]:
        local_stage: dict[str, float] = {}
        if reader is None:
            return (
                None,
                InsightsAggregationError(QUERY_LIMIT_EXCEEDED, "reader_required"),
                local_stage,
            )
        t_lake = time.perf_counter()
        try:
            plan = plan_overview_lake_query(
                window=DateWindow(
                    start_date=request.start_date_utc,
                    end_date=request.end_date_utc,
                ),
                lake_metrics=lake_ids,
            )
            _LOG.info(
                "insights_overview_lake_begin prefixes=%s streams=%s",
                len(plan.prefixes),
                ",".join(plan.streams),
            )
            result = reader.read_plan(plan)
            ctx = _context_from_reader_result(result)
            local_stage["lake_read"] = (time.perf_counter() - t_lake) * 1000.0
            local_stage["lake_lists"] = float(result.diagnostics.list_requests)
            local_stage["lake_gets"] = float(result.diagnostics.get_requests)
            local_stage["lake_objects"] = float(result.diagnostics.objects_considered)
            _LOG.info(
                "insights_overview_lake_done lake_ms=%.1f lists=%.0f gets=%.0f objs=%.0f",
                local_stage["lake_read"],
                local_stage["lake_lists"],
                local_stage["lake_gets"],
                local_stage["lake_objects"],
            )
            return ctx, None, local_stage
        except InsightsAggregationError as exc:
            local_stage["lake_read"] = (time.perf_counter() - t_lake) * 1000.0
            _LOG.info(
                "insights_overview_lake_error lake_ms=%.1f detail=%s",
                local_stage["lake_read"],
                exc.detail,
            )
            return None, exc, local_stage
        except Exception:
            local_stage["lake_read"] = (time.perf_counter() - t_lake) * 1000.0
            _LOG.info(
                "insights_overview_lake_error lake_ms=%.1f detail=lake_failed",
                local_stage["lake_read"],
            )
            return (
                None,
                InsightsAggregationError(QUERY_LIMIT_EXCEEDED, "lake_failed"),
                local_stage,
            )

    def _external_work(mid: str) -> tuple[str, MetricResult, float]:
        req = MetricRequest(mid, request.start_date_utc, request.end_date_utc)
        t_ext = time.perf_counter()
        result = aggregate_metric(
            req,
            validation_catalog=validation_catalog,
            published_reports_port=published_reports_port,
            community_sentiment_port=community_sentiment_port,
        )
        return mid, result, (time.perf_counter() - t_ext) * 1000.0

    workers = max(1, (1 if lake_ids else 0) + len(external_ids))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        lake_fut = pool.submit(_lake_work) if lake_ids else None
        ext_futs = [pool.submit(_external_work, mid) for mid in external_ids]
        if lake_fut is not None:
            lake_ctx, lake_error, lake_stage = lake_fut.result()
            stage_ms.update(lake_stage)
        for fut in as_completed(ext_futs):
            mid, result, ms = fut.result()
            external_results[mid] = result
            stage_ms[f"ext_{mid}"] = ms

    ordered: list[MetricResult] = []
    for mid in metric_ids:
        req = MetricRequest(mid, request.start_date_utc, request.end_date_utc)
        if mid not in SUPPORTED_METRICS:
            ordered.append(
                MetricResult(
                    metric_id=mid,
                    status="error",
                    window=MetricWindow(
                        request.start_date_utc, request.end_date_utc, "bounded_period"
                    ),
                    value=None,
                    completeness="unavailable",
                    limitations=finalize_limitations(["source_unavailable"]),
                )
            )
            continue
        if mid in EXTERNAL_METRICS or is_external_metric(mid):
            ordered.append(external_results[mid])
            continue
        if lake_error is not None:
            ordered.append(_error_result(mid, req, lake_error))
            continue
        assert lake_ctx is not None
        try:
            ordered.append(
                AGGREGATORS[mid](
                    lake_ctx,
                    request.start_date_utc,
                    request.end_date_utc,
                )
            )
        except InsightsAggregationError as exc:
            ordered.append(_error_result(mid, req, exc))
        except Exception:
            ordered.append(
                MetricResult(
                    metric_id=mid,
                    status="error",
                    window=MetricWindow(
                        request.start_date_utc, request.end_date_utc, "bounded_period"
                    ),
                    value=None,
                    completeness="unavailable",
                    limitations=finalize_limitations(["source_unavailable"]),
                )
            )

    stage_ms["total"] = (time.perf_counter() - t0) * 1000.0
    timing_line = (
        "insights_overview_timing total_ms=%.1f lake_ms=%.1f lists=%.0f gets=%.0f "
        "objs=%.0f github_ms=%.1f published_ms=%.1f sentiment_ms=%.1f"
        % (
            stage_ms.get("total", 0.0),
            stage_ms.get("lake_read", 0.0),
            stage_ms.get("lake_lists", 0.0),
            stage_ms.get("lake_gets", 0.0),
            stage_ms.get("lake_objects", 0.0),
            stage_ms.get("ext_github_stars", 0.0) + stage_ms.get("ext_github_forks", 0.0),
            stage_ms.get("ext_published_reports", 0.0),
            stage_ms.get("ext_community_sentiment", 0.0),
        )
    )
    _LOG.info(timing_line)
    print(timing_line, flush=True)
    return tuple(ordered)


def _plan(metric_id: str, start: date, end: date) -> QueryPlan:
    try:
        return plan_metric_query(
            metric=metric_id, window=DateWindow(start_date=start, end_date=end)
        )
    except InsightsQueryPlanError as exc:
        if exc.code == "invalid_query_window":
            raise InsightsAggregationError(INVALID_WINDOW, exc.detail) from None
        raise InsightsAggregationError(INVALID_METRIC, exc.detail) from None


def _load_context(
    *,
    metric_id: str,
    start: date,
    end: date,
    reader: BoundedS3Reader | None,
) -> AggregationContext:
    if reader is None:
        raise InsightsAggregationError(QUERY_LIMIT_EXCEEDED, "reader_required")
    plan = _plan(metric_id, start, end)
    return _context_from_reader_result(reader.read_plan(plan))


def _context_from_reader_result(result: ReaderResult) -> AggregationContext:
    ctx = AggregationContext(diagnostics=result.diagnostics)
    for obj in result.objects:
        envelope = decode_object_bytes(obj.body)
        if envelope is None:
            ctx.diagnostics.malformed_objects += 1
            continue
        event = normalize_event(envelope)
        if event is None:
            schema = envelope.get("envelope_schema_version")
            if schema != "1.0":
                ctx.diagnostics.unsupported_schema_objects += 1
            else:
                ctx.diagnostics.malformed_objects += 1
            continue
        ctx.events.append(event)
    return ctx


def _error_result(
    metric_id: str, request: MetricRequest, exc: InsightsAggregationError
) -> MetricResult:
    completeness = "unavailable"
    lim = ["source_unavailable"]
    if exc.code == QUERY_LIMIT_EXCEEDED:
        # reader_required is a wiring defect, not an S3 list/get budget hit.
        if exc.detail == "reader_required":
            completeness = "unavailable"
            lim = ["source_unavailable", "aggregation_reader_unwired"]
        else:
            completeness = "partial"
            lim = ["query_budget_reached"]
    elif exc.code == INVALID_WINDOW:
        completeness = "unavailable"
        lim = ["source_unavailable"]
    return MetricResult(
        metric_id=metric_id,
        status="error",
        window=MetricWindow(
            request.start_date_utc, request.end_date_utc, "bounded_period"
        ),
        value=None,
        completeness=completeness,  # type: ignore[arg-type]
        limitations=finalize_limitations(lim),
    )
