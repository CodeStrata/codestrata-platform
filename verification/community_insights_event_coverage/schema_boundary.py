"""Schema activation boundary for Slice 15.3."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_insights_event_coverage.policy import load_coverage_policy


def schema_boundary(monorepo: Path) -> dict[str, Any]:
    policy = load_coverage_policy(monorepo)
    return {
        "schema_activation_allowed_in_15_3": policy.get(
            "schema_activation_allowed_in_15_3"
        )
        is False,
        "runtime_ingestion_changes_allowed": policy.get(
            "runtime_ingestion_changes_allowed"
        )
        is False,
        "path_layout_unchanged": policy.get("path_layout_unchanged") is True,
    }
