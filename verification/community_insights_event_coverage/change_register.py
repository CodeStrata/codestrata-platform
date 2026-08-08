"""Future schema change register (not activated in 15.3)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_insights_event_coverage.policy import load_coverage_policy


def load_change_register(monorepo: Path) -> list[dict[str, Any]]:
    policy = load_coverage_policy(monorepo)
    rows = list(policy.get("change_register") or [])
    for row in rows:
        assert row.get("status") == "implemented_in_15_4"
    return sorted(rows, key=lambda r: r.get("change_id") or "")
