"""Policy loader."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_insights_ingestion.contract import POLICY_RELATIVE
from verification.community_insights_ingestion.inventory import load_json


def load_ingestion_policy(monorepo: Path) -> dict[str, Any]:
    return load_json(monorepo, POLICY_RELATIVE)
