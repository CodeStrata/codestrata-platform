"""Regression: Insights list budget must cover day×stream prefix plans."""

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
    assert len(plan.prefixes) == 155  # 31 days × 5 streams
    assert plan.budgets.max_list_requests_per_query >= len(plan.prefixes)
