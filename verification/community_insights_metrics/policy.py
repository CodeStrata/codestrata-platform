"""Policy loader for Slice 15.6."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_insights_metrics.contract import POLICY_RELATIVE
from verification.community_insights_metrics.inventory import load_json


def load_metrics_policy(monorepo: Path) -> dict[str, Any]:
    return load_json(monorepo, POLICY_RELATIVE)
