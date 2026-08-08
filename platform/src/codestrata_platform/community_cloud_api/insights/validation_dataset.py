"""External validation catalog adapter (local repository artifact)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from codestrata_platform.community_cloud_api.insights.completeness import finalize_limitations
from codestrata_platform.community_cloud_api.insights.errors import (
    EXTERNAL_SOURCE_UNAVAILABLE,
    InsightsAggregationError,
)
from codestrata_platform.community_cloud_api.insights.models import MetricResult, MetricWindow
from datetime import date


class ValidationCatalogPort(Protocol):
    def repository_count(self) -> int: ...


class LocalValidationCatalogReader:
    """Reads validation/repository-catalog/catalog.json from a monorepo root."""

    def __init__(self, monorepo_root: Path) -> None:
        self._path = monorepo_root / "validation" / "repository-catalog" / "catalog.json"

    def repository_count(self) -> int:
        if not self._path.is_file():
            raise InsightsAggregationError(EXTERNAL_SOURCE_UNAVAILABLE, "catalog_missing")
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            raise InsightsAggregationError(EXTERNAL_SOURCE_UNAVAILABLE, "catalog_unreadable")
        repos = data.get("repositories")
        if not isinstance(repos, list):
            raise InsightsAggregationError(EXTERNAL_SOURCE_UNAVAILABLE, "catalog_shape")
        return len(repos)


def aggregate_validation_dataset(
    reader: ValidationCatalogPort,
    *,
    start: date,
    end: date,
) -> MetricResult:
    try:
        count = reader.repository_count()
    except InsightsAggregationError:
        return MetricResult(
            metric_id="validation_dataset_growth",
            status="error",
            window=MetricWindow(start, end, "external"),
            value=None,
            completeness="unavailable",
            limitations=finalize_limitations(
                [
                    "source_unavailable",
                    "validation_growth_snapshots_unavailable",
                    "production_ingestion_still_unwired",
                    "no_live_dashboard_data_claim",
                ]
            ),
        )
    return MetricResult(
        metric_id="validation_dataset_growth",
        status="ok",
        window=MetricWindow(start, end, "external"),
        value=count,
        completeness="complete",
        limitations=finalize_limitations(
            [
                "validation_growth_snapshots_unavailable",
                "production_ingestion_still_unwired",
                "no_live_dashboard_data_claim",
            ]
        ),
    )
