from pathlib import Path
from typing import Any
from verification.community_insights_aggregation.inventory import load_json
from verification.community_insights_aggregation.contract import POLICY_RELATIVE

def load_aggregation_policy(monorepo: Path) -> dict[str, Any]:
    return load_json(monorepo, POLICY_RELATIVE)
