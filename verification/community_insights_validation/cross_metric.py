"""Cross-metric consistency checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_validation._common import add_check, ensure_platform_importable
from verification.community_insights_validation.fixtures import bounded_reader, metric_window
from verification.community_insights_validation.models import CheckResult, Defect


def check_cross_metric(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ensure_platform_importable(monorepo)
    from codestrata_platform.community_cloud_api.insights.models import (
        MetricRequest,
        OverviewRequest,
    )
    from codestrata_platform.community_cloud_api.insights.service import (
        InsightsAggregationService,
        aggregate_metric,
    )
    from codestrata_platform.community_cloud_api.insights.validation_dataset import (
        LocalValidationCatalogReader,
    )

    reader, _fx = bounded_reader(monorepo)
    start, end = metric_window()

    single = aggregate_metric(
        MetricRequest("successful_assessments", start, end),
        reader=reader,
    )
    svc = InsightsAggregationService(
        reader=reader,
        validation_catalog=LocalValidationCatalogReader(monorepo),
    )
    overview = svc.aggregate_dashboard_overview(
        OverviewRequest(start, end, metric_ids=("successful_assessments",))
    )
    add_check(
        checks,
        defects,
        "cross_metric:overview_matches_single",
        len(overview) == 1
        and overview[0].metric_id == "successful_assessments"
        and overview[0].value == single.value,
        f"overview={overview[0].value},single={single.value}",
        "metric_correctness",
    )
    return checks, defects
