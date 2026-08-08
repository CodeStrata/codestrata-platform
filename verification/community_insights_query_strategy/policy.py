from verification.community_insights_query_strategy.inventory import load_json
from verification.community_insights_query_strategy.contract import POLICY_RELATIVE
from pathlib import Path
from typing import Any

def load_query_policy(monorepo: Path) -> dict[str, Any]:
    return load_json(monorepo, POLICY_RELATIVE)
