"""Suppression runtime checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_validation._common import add_check, ensure_platform_importable
from verification.community_insights_validation.fixtures import bounded_reader, metric_window
from verification.community_insights_validation.models import CheckResult, Defect


def check_suppression(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ensure_platform_importable(monorepo)
    from codestrata_platform.community_cloud_api.insights.models import MetricRequest
    from codestrata_platform.community_cloud_api.insights.policy import MINIMUM_GROUP_COUNT
    from codestrata_platform.community_cloud_api.insights.service import aggregate_metric
    from codestrata_platform.community_cloud_api.insights.suppression import suppress_groups

    groups, suppressed = suppress_groups(
        {"solo_provider": 1, "duo_provider": 2, "trio_provider": 3},
        dimension="provider_family",
        minimum=MINIMUM_GROUP_COUNT,
    )
    keys = {g.key for g in groups}
    add_check(
        checks,
        defects,
        "suppression:min_cohort_3",
        MINIMUM_GROUP_COUNT == 3 and suppressed,
        str(MINIMUM_GROUP_COUNT),
        "suppression",
    )
    add_check(
        checks,
        defects,
        "suppression:hide_count_1",
        "solo_provider" not in keys,
        "hidden",
        "suppression",
    )
    add_check(
        checks,
        defects,
        "suppression:hide_count_2",
        "duo_provider" not in keys,
        "hidden",
        "suppression",
    )
    add_check(
        checks,
        defects,
        "suppression:show_count_3",
        "trio_provider" in keys,
        "visible",
        "suppression",
    )
    add_check(
        checks,
        defects,
        "suppression:other_bucket",
        "other_suppressed" in keys,
        "present",
        "suppression",
    )

    reader, _fx = bounded_reader(monorepo)
    start, end = metric_window()
    result = aggregate_metric(
        MetricRequest("ai_provider_adoption", start, end),
        reader=reader,
    )
    group_keys = {g.key for g in result.groups}
    add_check(
        checks,
        defects,
        "suppression:runtime_provider_adoption",
        "solo_provider" not in group_keys and "duo_provider" not in group_keys,
        ",".join(sorted(group_keys)),
        "suppression",
    )
    return checks, defects
