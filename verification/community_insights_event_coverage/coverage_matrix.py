"""Metric coverage matrix builder."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_insights_event_coverage.contract import DASHBOARD_METRICS
from verification.community_insights_event_coverage.policy import load_coverage_policy


def build_metric_matrix(monorepo: Path) -> list[dict[str, Any]]:
    policy = load_coverage_policy(monorepo)
    coverage = policy.get("metric_coverage") or {}
    rows: list[dict[str, Any]] = []
    for metric in DASHBOARD_METRICS:
        entry = coverage.get(metric) or {}
        rows.append(
            {
                "metric": metric,
                "status": entry.get("status"),
                "source_streams": list(entry.get("source_streams") or []),
                "required_fields": list(entry.get("required_fields") or []),
                "privacy": entry.get("privacy"),
                "future_schema_enhancement_required": bool(
                    entry.get("future_schema_enhancement_required")
                ),
                "external_metric_source": bool(entry.get("external_metric_source")),
                "undercount_risk": entry.get("undercount_risk"),
                "schema_impact": entry.get("schema_impact"),
            }
        )
    return rows
