"""Failure isolation runtime checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_validation._common import add_check, ensure_platform_importable
from verification.community_insights_validation.fixtures import bounded_reader, metric_window
from verification.community_insights_validation.models import CheckResult, Defect


def check_failure_isolation(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ensure_platform_importable(monorepo)
    from codestrata_platform.community_cloud_api.insights.models import OverviewRequest
    from codestrata_platform.community_cloud_api.insights.service import InsightsAggregationService
    from codestrata_platform.community_cloud_api.insights.validation_dataset import (
        LocalValidationCatalogReader,
    )

    reader, _fx = bounded_reader(monorepo)
    start, end = metric_window()
    svc = InsightsAggregationService(
        reader=reader,
        validation_catalog=LocalValidationCatalogReader(monorepo),
    )
    results = svc.aggregate_dashboard_overview(
        OverviewRequest(
            start,
            end,
            metric_ids=(
                "successful_assessments",
                "validation_dataset_growth",
                "not_a_real_metric",
            ),
        )
    )
    add_check(
        checks,
        defects,
        "failure:isolates_invalid_metric",
        len(results) == 3 and results[2].status == "error",
        results[2].status,
        "metric_correctness",
    )
    add_check(
        checks,
        defects,
        "failure:valid_metrics_still_ok",
        results[0].status == "ok" and results[1].status == "ok",
        "ok",
        "metric_correctness",
    )
    return checks, defects
