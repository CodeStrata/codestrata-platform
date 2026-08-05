"""Infrastructure contract checks for completion verification (Slice 8.15)."""

from __future__ import annotations

from verification.community_data_lake.infrastructure import (
    check_infrastructure_static,
    check_opentofu,
)
from verification.community_data_lake_completion.models import CheckResult


def check_infrastructure(*, run_opentofu: bool = True) -> tuple[str, list[CheckResult]]:
    static = [
        CheckResult(
            name=item.name.replace("infra:", "completion:infra:"),
            ok=item.ok,
            detail=item.detail,
            category="infrastructure",
            scenario=item.scenario,
        )
        for item in check_infrastructure_static()
    ]
    opentofu_status, opentofu_checks, _warnings = check_opentofu(run_opentofu=run_opentofu)
    opentofu = [
        CheckResult(
            name=item.name.replace("opentofu:", "completion:opentofu:"),
            ok=item.ok,
            detail=item.detail,
            category="opentofu",
            scenario=item.scenario,
        )
        for item in opentofu_checks
    ]
    status = opentofu_status if run_opentofu else "skipped"
    return status, static + opentofu


__all__ = ["check_infrastructure"]
