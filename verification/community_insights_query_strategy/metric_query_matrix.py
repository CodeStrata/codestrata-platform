from verification.community_insights_query_strategy.contract import LAKE_METRICS
from verification.community_insights_query_strategy.policy import load_query_policy
from pathlib import Path
from typing import Any

def matrix_rows(monorepo: Path) -> list[dict[str, Any]]:
    m = load_query_policy(monorepo).get("metric_query_matrix") or {}
    rows=[]
    for metric in LAKE_METRICS:
        e=m.get(metric) or {}
        rows.append({"metric": metric, "streams": list(e.get("streams") or []), "direct_s3_suitable": e.get("direct_s3_suitable"), "future_checkpoint": e.get("future_checkpoint")})
    ext=m.get("validation_dataset_growth") or {}
    rows.append({"metric":"validation_dataset_growth","streams":[],"query_strategy":ext.get("query_strategy"),"s3_query":ext.get("s3_query")})
    return rows
