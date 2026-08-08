"""Metric catalog identity list."""

from __future__ import annotations

from verification.community_insights_event_coverage.contract import DASHBOARD_METRICS


def all_metric_ids() -> tuple[str, ...]:
    return DASHBOARD_METRICS
