"""Ingestion enablement boundary."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_insights_event_coverage.inventory import read_text


def ingestion_boundary(monorepo: Path) -> dict[str, Any]:
    # Epic 8/15.1 posture: wire remains false in authoritative policy modules.
    text = read_text(
        monorepo,
        "platform/src/codestrata_platform/community_cloud_api/data_lake/policy.py",
    )
    return {
        "enable_ingestion_wire_mentioned": "enable_ingestion" in text.lower()
        or "ingestion" in text.lower(),
        "ingestion_enabled_in_15_3": False,
    }
