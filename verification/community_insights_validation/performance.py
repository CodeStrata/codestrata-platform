"""Performance posture checks (offline)."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_validation._common import add_check, ensure_platform_importable
from verification.community_insights_validation.fixtures import bounded_reader, metric_window
from verification.community_insights_validation.models import CheckResult, Defect


def check_performance(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
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
    results = svc.aggregate_dashboard_overview(OverviewRequest(start, end))
    add_check(
        checks,
        defects,
        "performance:overview_batch_completes",
        len(results) >= 10,
        str(len(results)),
        "metric_correctness",
    )
    return checks, defects
