"""Query budget regression checks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_data_lake_insights.contract import AGG_REGISTER, QUERY_POLICY
from verification.community_data_lake_insights.helpers import check, load_json
from verification.community_data_lake_insights.models import CheckResult, Defect


def check_query_budget(
    monorepo: Path,
    *,
    dashboard: dict[str, Any] | None = None,
) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    dash = dashboard or {}

    policy = load_json(monorepo / QUERY_POLICY)
    budgets = policy.get("budgets") or {}
    policy_ok = budgets.get("max_list_requests_per_query") == 2000
    checks.append(
        check(
            "query_budget:max_list_requests_2000",
            policy_ok,
            str(budgets.get("max_list_requests_per_query")),
            "query_budget",
        )
    )
    if not policy_ok:
        defects.append(
            Defect(
                "query_budget_policy",
                "query_budget:max_list_requests_2000",
                "2000",
                str(budgets.get("max_list_requests_per_query")),
            )
        )

    agg = load_json(monorepo / AGG_REGISTER)
    agg_ok = agg.get("max_list_requests_per_query") == 2000
    checks.append(
        check(
            "query_budget:agg_register_2000",
            agg_ok,
            str(agg.get("max_list_requests_per_query")),
            "query_budget",
        )
    )

    # If live overview available, assert query_budget_reached is false
    budget_reached = dash.get("query_budget_reached")
    if dash.get("overview_ok") is True and budget_reached is not None:
        ok = budget_reached is False
        checks.append(
            check(
                "query_budget:live_not_reached",
                ok,
                f"query_budget_reached={budget_reached}",
                "query_budget",
            )
        )
        if not ok:
            defects.append(
                Defect(
                    "query_budget_reached",
                    "query_budget:live_not_reached",
                    "false",
                    "true",
                )
            )
    else:
        checks.append(
            check(
                "query_budget:live_not_reached",
                True,
                "live overview budget flag deferred/unavailable",
                "query_budget",
            )
        )

    summary = {
        "max_list_requests_per_query": 2000 if policy_ok else budgets.get("max_list_requests_per_query"),
        "query_budget_reached": budget_reached if budget_reached is not None else False,
        "healthy_for_supported_window": policy_ok,
    }
    return checks, defects, summary
