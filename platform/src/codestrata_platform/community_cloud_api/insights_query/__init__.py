"""Bounded Insights S3 query planning (Slice 15.5).

SDK-free, network-free, credential-free prefix planning for future
on-demand aggregation. Does not list or read objects.
"""

from __future__ import annotations

from codestrata_platform.community_cloud_api.insights_query.errors import (
    InsightsQueryPlanError,
)
from codestrata_platform.community_cloud_api.insights_query.models import (
    DateWindow,
    QueryBudgets,
    QueryPlan,
)
from codestrata_platform.community_cloud_api.insights_query.planner import (
    plan_metric_query,
    plan_overview_lake_query,
    plan_prefixes,
)
from codestrata_platform.community_cloud_api.insights_query.policy import (
    COMMUNITY_INSIGHTS_QUERY_POLICY_ID,
    COMMUNITY_INSIGHTS_QUERY_POLICY_VERSION,
    default_query_budgets,
)

__all__ = [
    "COMMUNITY_INSIGHTS_QUERY_POLICY_ID",
    "COMMUNITY_INSIGHTS_QUERY_POLICY_VERSION",
    "DateWindow",
    "InsightsQueryPlanError",
    "QueryBudgets",
    "QueryPlan",
    "default_query_budgets",
    "plan_metric_query",
    "plan_overview_lake_query",
    "plan_prefixes",
]
