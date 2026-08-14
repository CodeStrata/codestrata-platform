"""Regression: Insights list budget must cover month×stream prefix plans."""

from __future__ import annotations

from datetime import date, timedelta

from codestrata_platform.community_cloud_api.insights_query.models import DateWindow
from codestrata_platform.community_cloud_api.insights_query.planner import plan_metric_query


def test_list_budget_covers_multistream_bounded_window() -> None:
    end = date(2026, 8, 9)
    start = end - timedelta(days=30)
    plan = plan_metric_query(
        metric="total_anonymous_installations",
        window=DateWindow(start_date=start, end_date=end),
    )
    # Jul+Aug × (4 streams @ schema 1.0 + assessment_metadata @ 1.0+1.1) = 2 × 6 = 12
    assert len(plan.prefixes) == 12
    assert plan.budgets.max_list_requests_per_query >= len(plan.prefixes)
