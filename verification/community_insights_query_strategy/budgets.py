from verification.community_insights_query_strategy.policy import load_query_policy
from pathlib import Path
from typing import Any

def budgets(monorepo: Path) -> dict[str, Any]:
    return dict(load_query_policy(monorepo).get("budgets") or {})
