"""CR-15.3-* disposition helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_insights_ingestion.policy import load_ingestion_policy


def dispositions(monorepo: Path) -> dict[str, Any]:
    return dict(load_ingestion_policy(monorepo).get("change_register_disposition") or {})
