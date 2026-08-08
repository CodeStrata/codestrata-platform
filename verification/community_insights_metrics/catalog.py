"""Metric catalog helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_insights_metrics.contract import METRIC_IDS, POLICY_RELATIVE
from verification.community_insights_metrics.inventory import load_json

__all__ = ["METRIC_IDS", "catalog_entry", "all_metric_ids"]


def all_metric_ids() -> tuple[str, ...]:
    return METRIC_IDS


def catalog_entry(monorepo: Path, metric_id: str) -> dict[str, Any]:
    policy = load_json(monorepo, POLICY_RELATIVE)
    return (policy.get("metric_catalog") or {}).get(metric_id) or {}
