"""Community Insights aggregation domain (Slice 15.7) — boto3-free."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.insights.errors import InsightsAggregationError
from codestrata_platform.community_cloud_api.insights.models import (
    MetricGroup,
    MetricRequest,
    MetricResult,
    MetricWindow,
    OverviewRequest,
    ReadDiagnostics,
)
from codestrata_platform.community_cloud_api.insights.service import (
    InsightsAggregationService,
    aggregate_dashboard_overview,
    aggregate_metric,
)

COMMUNITY_INSIGHTS_AGGREGATION_POLICY_ID = "community-insights-aggregation-policy"
COMMUNITY_INSIGHTS_AGGREGATION_POLICY_VERSION = "1.0"

__all__ = [
    "COMMUNITY_INSIGHTS_AGGREGATION_POLICY_ID",
    "COMMUNITY_INSIGHTS_AGGREGATION_POLICY_VERSION",
    "InsightsAggregationError",
    "InsightsAggregationService",
    "MetricGroup",
    "MetricRequest",
    "MetricResult",
    "MetricWindow",
    "OverviewRequest",
    "ReadDiagnostics",
    "aggregate_dashboard_overview",
    "aggregate_metric",
]
