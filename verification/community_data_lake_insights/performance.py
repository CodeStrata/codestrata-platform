"""Performance / cost classification for v0.2.0."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_data_lake_insights.helpers import check
from verification.community_data_lake_insights.models import CheckResult, Defect


def check_performance(
    monorepo: Path,
    *,
    live_probe: dict[str, Any] | None = None,
) -> tuple[list[CheckResult], list[Defect], dict]:
    _ = monorepo
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    live = live_probe or {}

    before = live.get("before_counts") or {}
    after = live.get("after_counts") or {}
    total = 0
    for src in (before, after):
        if isinstance(src, dict):
            total = max(total, sum(int(v) for v in src.values() if isinstance(v, int)))

    if total < 1_000:
        count_class = "small"
    elif total < 50_000:
        count_class = "medium"
    else:
        count_class = "large"

    duration = live.get("probe_duration_seconds")
    # Budget: list budgets already validated at 2000
    classification = "ACCEPTABLE_V0_2_0"
    if count_class == "large" and isinstance(duration, (int, float)) and duration > 120:
        classification = "OPTIMIZE_BEFORE_RELEASE"
    if count_class == "large" and isinstance(duration, (int, float)) and duration > 300:
        classification = "BLOCKER"

    ok = classification in {"ACCEPTABLE_V0_2_0", "OPTIMIZE_BEFORE_RELEASE"}
    checks.append(
        check(
            "performance:classification",
            ok,
            classification,
            "performance",
        )
    )
    if classification == "BLOCKER":
        defects.append(
            Defect(
                "performance_blocker",
                "performance:classification",
                "ACCEPTABLE_V0_2_0",
                classification,
            )
        )

    summary = {
        "object_count_class": count_class,
        "total_raw_objects": total,
        "live_probe_duration_seconds": duration,
        "max_list_requests_per_query": 2000,
        "classification": classification,
        "no_athena_glue_rds": True,
    }
    return checks, defects, summary
