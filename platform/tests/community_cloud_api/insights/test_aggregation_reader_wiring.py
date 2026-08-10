"""Regression: Insights aggregation must be wired with a bounded S3 reader."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.insights.errors import (
    QUERY_LIMIT_EXCEEDED,
    InsightsAggregationError,
)
from codestrata_platform.community_cloud_api.insights.models import MetricRequest, OverviewRequest
from codestrata_platform.community_cloud_api.insights.service import (
    InsightsAggregationService,
    _error_result,
)
from datetime import date


def test_reader_required_is_not_query_budget() -> None:
    req = MetricRequest(
        metric_id="total_anonymous_installations",
        start_date_utc=date(2026, 7, 11),
        end_date_utc=date(2026, 8, 9),
    )
    result = _error_result(
        "total_anonymous_installations",
        req,
        InsightsAggregationError(QUERY_LIMIT_EXCEEDED, "reader_required"),
    )
    assert "query_budget_reached" not in result.limitations
    assert "aggregation_reader_unwired" in result.limitations
    assert result.status == "error"


def test_unwired_service_marks_reader_defect_not_budget() -> None:
    service = InsightsAggregationService()  # reader=None
    results = service.aggregate_dashboard_overview(
        OverviewRequest(
            start_date_utc=date(2026, 7, 11),
            end_date_utc=date(2026, 8, 9),
            metric_ids=("successful_assessments",),
        )
    )
    assert len(results) == 1
    assert "query_budget_reached" not in results[0].limitations
    assert "aggregation_reader_unwired" in results[0].limitations
