"""Runtime metric correctness checks."""

from __future__ import annotations

import json
from pathlib import Path

from verification.community_insights_validation._common import add_check, ensure_platform_importable
from verification.community_insights_validation.fixtures import (
    build_fixtures,
    bounded_reader,
    metric_window,
)
from verification.community_insights_validation.models import CheckResult, Defect


def check_metric_correctness(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ensure_platform_importable(monorepo)
    from codestrata_platform.community_cloud_api.insights.models import MetricRequest
    from codestrata_platform.community_cloud_api.insights.service import aggregate_metric

    reader, fx = bounded_reader(monorepo)
    start, end = metric_window()

    result = aggregate_metric(
        MetricRequest("total_anonymous_installations", start, end),
        reader=reader,
    )
    add_check(
        checks,
        defects,
        "metric:installations_not_events",
        result.value == fx.expected_installations,
        f"value={result.value}",
        "metric_correctness",
    )
    add_check(
        checks,
        defects,
        "metric:installations_not_equal_events",
        result.value != fx.expected_events,
        f"installs={result.value},events={fx.expected_events}",
        "metric_correctness",
    )

    stable = json.dumps(result.to_stable_dict())
    for poison in fx.poison_strings:
        add_check(
            checks,
            defects,
            f"metric:stable_no_{poison[:12]}",
            poison not in stable,
            "absent",
            "privacy",
        )
    return checks, defects
