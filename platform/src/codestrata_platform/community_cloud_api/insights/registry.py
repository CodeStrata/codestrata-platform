"""Metric registry — fail closed on unknown metrics."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.insights.aggregators import AGGREGATORS, Aggregator
from codestrata_platform.community_cloud_api.insights.errors import (
    INVALID_METRIC,
    InsightsAggregationError,
)
from codestrata_platform.community_cloud_api.insights.policy import (
    METRIC_HORIZONS,
    SUPPORTED_METRICS,
)
from codestrata_platform.community_cloud_api.insights_query.policy import (
    EXTERNAL_METRICS,
    METRIC_STREAMS,
)


def get_aggregator(metric_id: str) -> Aggregator:
    if metric_id not in SUPPORTED_METRICS:
        raise InsightsAggregationError(INVALID_METRIC, "unknown")
    if metric_id in EXTERNAL_METRICS:
        raise InsightsAggregationError(INVALID_METRIC, "use_external_adapter")
    agg = AGGREGATORS.get(metric_id)
    if agg is None:
        raise InsightsAggregationError(INVALID_METRIC, "unregistered")
    return agg


def streams_for_metric(metric_id: str) -> tuple[str, ...]:
    if metric_id not in SUPPORTED_METRICS:
        raise InsightsAggregationError(INVALID_METRIC, "unknown")
    if metric_id in EXTERNAL_METRICS:
        return ()
    streams = METRIC_STREAMS.get(metric_id)
    if streams is None:
        raise InsightsAggregationError(INVALID_METRIC, "no_streams")
    return streams


def horizon_for_metric(metric_id: str) -> str:
    return METRIC_HORIZONS.get(metric_id, "bounded_period")


def is_external_metric(metric_id: str) -> bool:
    return metric_id in EXTERNAL_METRICS
